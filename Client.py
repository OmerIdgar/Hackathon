from socket import *
from struct import *
import sys

BUFFER_SIZE = 1024


class Client:

    def __init__(self, team_name, port, magic_cookie, message_type):
        self.team_name = team_name
        self.port = port
        self.magic_cookie = magic_cookie
        self.message_type = message_type
        self.connected = False
        self.sock = None

    def open_udp_socket(self):
        try:
            self.sock = socket(AF_INET, SOCK_DGRAM)
            self.sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            # sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.sock.bind(("", self.port))
            self.connected = True
        except error:
            self.connected = False
            if self.sock:
                self.close_socket()
            sys.exit(1)

    def close_socket(self):
        self.sock.close()

    def is_valid_packet(self, magic_cookie, message_type):
        is_valid_cookie = magic_cookie == self.magic_cookie
        is_valid_type = message_type == self.message_type
        return is_valid_cookie and is_valid_type

    def get_server_broadcast(self):
        while self.connected:
            data, server_address = socket.recvfrom(BUFFER_SIZE)
            magic_cookie, message_type, server_port = unpack('IcH', data)
            if not self.is_valid_packet(magic_cookie, message_type):
                continue
            print(f"Received offer from {server_address}, attempting to connect...")
            return server_address, server_port

    def connect_server(self, server_address, server_port):
        with socket(AF_INET, SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((server_address, server_port))
            send_data = self.team_name + "\n"
            tcp_socket.sendall(send_data.encode())
            welcome_message = tcp_socket.recv(1024).decode()
            print(welcome_message)
            answer = sys.stdin.read(1)
            tcp_socket.sendall(answer.encode())
            summary_message = tcp_socket.recv(1024).decode()
            print(summary_message)

    def run(self):
        print("Client started, listening for offer requests...")
        while True:
            self.open_udp_socket()
            server_address, server_port = self.get_server_broadcast()
            self.connect_server(server_address, server_port)
            print("Server disconnected, listening for offer requests...")
