import requests
import socket
import socks
from concurrent.futures import ThreadPoolExecutor

def check_proxy(proxy):
    ip, port = proxy.split(':')
    socks.setdefaultproxy(socks.SOCKS5, ip, int(port))
    socket.socket = socks.socksocket
    try:
        response = requests.get("http://httpbin.org/ip", timeout=5)
        if response.status_code == 200:
            print(f"[+] Working proxy: {proxy}")
            return proxy
    except Exception as e:
        print(f"[-] Bad proxy: {proxy} | Error: {e}")
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
    
    working_proxies = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(check_proxy, proxies)
        working_proxies = [proxy for proxy in results if proxy]
    
    save_working_proxies(working_proxies)
    print(f"[*] Saved {len(working_proxies)} working proxies to live-proxies.txt")

if __name__ == "__main__":
    main()
