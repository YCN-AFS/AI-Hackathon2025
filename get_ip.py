import socket

def get_ip():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    print(f"Hostname: {hostname}")
    print(f"IP Address: {ip}")

if __name__ == "__main__":
    get_ip() 