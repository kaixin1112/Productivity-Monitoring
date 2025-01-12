import socket
import time

def udp_sender(target_ip, target_port, message):
    """Send a UDP message to a specified target IP and port."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender_socket:
        sender_socket.sendto(message.encode('utf-8'), (target_ip, target_port))

if __name__ == "__main__":

    udp_sender("192.168.43.58", 12345, 'Alert')