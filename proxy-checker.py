import socket
import socks
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

CHUNK_SIZE = 1000
STATS_LOCK = threading.Lock()
stats = {"good": 0, "bad": 0, "remaining": 0, "total": 0}

def check_proxy(proxy):
    ip, port = proxy.split(':')
    socks.setdefaultproxy(socks.SOCKS5, ip, int(port))
    socket.socket = socks.socksocket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(5)
            s.connect(("8.8.8.8", 53))
        with STATS_LOCK:
            stats["good"] += 1
            stats["remaining"] -= 1
        return proxy
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        with STATS_LOCK:
            stats["bad"] += 1
            stats["remaining"] -= 1
        return None

def save_working_proxies(working_proxies, filename="live-proxies.txt"):
    with open(filename, "a") as f:
        for proxy in working_proxies:
            f.write(proxy + "\n")

def split_file(filename="proxies.txt", chunk_size=CHUNK_SIZE):
    """Splits proxies.txt into smaller chunk files of size 1000 each."""
    with open(filename, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]
    
    stats["total"] = len(proxies)
    stats["remaining"] = len(proxies)

    if not proxies:
        print("[!] No proxies found in proxies.txt")
        return []

    chunk_files = []
    for i in range(0, len(proxies), chunk_size):
        chunk_filename = f"chunk_{i//chunk_size}.txt"
        chunk_files.append(chunk_filename)
        with open(chunk_filename, "w") as chunk_file:
            chunk_file.write("\n".join(proxies[i:i+chunk_size]))

    return chunk_files

def process_chunk(chunk_filename):
    """Processes a single chunk file, checking proxies and saving live ones."""
    with open(chunk_filename, "r") as f:
        proxies = [line.strip() for line in f if line.strip()]

    working_proxies = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(check_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(future_to_proxy):
            proxy = future_to_proxy[future]
            try:
                result = future.result()
                if result:
                    working_proxies.append(result)
            except Exception as e:
                print(f"Error checking proxy {proxy}: {e}")

    save_working_proxies(working_proxies)
    os.remove(chunk_filename)  # Delete chunk file after processing

def display_stats():
    """Continuously prints real-time stats."""
    while stats["remaining"] > 0:
        with STATS_LOCK:
            print(f"\r[*] Total: {stats['total']} | Remaining: {stats['remaining']} | Working: {stats['good']} | Bad: {stats['bad']}", end="", flush=True)
    print("\n")  # Ensure proper formatting when finished

def main():
    try:
        chunk_files = split_file()
        if not chunk_files:
            return

        print(f"[*] Split into {len(chunk_files)} chunks of {CHUNK_SIZE} proxies each.")
        
        # Start async stats display
        stats_thread = threading.Thread(target=display_stats, daemon=True)
        stats_thread.start()

        for chunk in chunk_files:
            process_chunk(chunk)

        print(f"\n[*] Scan complete. Working proxies saved to live-proxies.txt.")
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user. Exiting gracefully...")
    except Exception as e:
        print(f"[!] An error occurred: {e}")

if __name__ == "__main__":
    main()
