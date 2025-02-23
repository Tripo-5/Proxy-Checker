import socket
import socks
from concurrent.futures import ThreadPoolExecutor

def check_proxy(proxy, stats):
    ip, port = proxy.split(':')
    socks.setdefaultproxy(socks.SOCKS5, ip, int(port))
    socket.socket = socks.socksocket
    try:
        # Try to connect to Google's DNS server (8.8.8.8:53)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(("8.8.8.8", 53))
            s.settimeout(5)
            stats["good"] += 1
            return proxy
    except Exception:
        stats["bad"] += 1
        return None

def load_proxies(filename="proxies.txt"):
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

def save_working_proxies(working_proxies, filename="live-proxies.txt"):
    with open(filename, "w") as f:
        for proxy in working_proxies:
            f.write(proxy + "\n")

def main():
    proxies = load_proxies()
    print(f"[*] Loaded {len(proxies)} proxies.")

    # Initialize stats dictionary
    stats = {
        "good": 0,
        "bad": 0,
        "total": len(proxies),
        "to_test": len(proxies)
    }

    working_proxies = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(lambda proxy: check_proxy(proxy, stats), proxies)
        working_proxies = [proxy for proxy in results if proxy]

    save_working_proxies(working_proxies)

    # Final output of stats after processing all proxies
    print(f"\n[*] Total proxies: {stats['total']}")
    print(f"[*] Proxies to test: {stats['to_test']}")
    print(f"[*] Working proxies: {stats['good']}")
    print(f"[*] Bad proxies: {stats['bad']}")
    print(f"[*] Saved {len(working_proxies)} working proxies to live-proxies.txt")

if __name__ == "__main__":
    main()
