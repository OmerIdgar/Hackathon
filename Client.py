from socket import *
from struct import *
import sys
import getch

BUFFER_SIZE = 1024


class Client:
    """
    A class represent a Client

    Attributes
    __________
    team_name : str
        the name of the team
    port : int
        the port number that the client is using
    magic_cookie
        client's unique value
    message_type
        client's unique value
    connected : boolean
        represent whether the client is connected to udp socket
    sock : socket
        represent the udp socket of the client
    """

    def __init__(self, team_name, port, magic_cookie, message_type):
        self.team_name = team_name
        self.port = port
        self.magic_cookie = magic_cookie
        self.message_type = message_type
        self.connected = False
        self.sock = None

    def open_udp_socket(self):
        """
        Open a udp socket for the client
        """
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
        """
        Close the udp socket of the client
        """
        self.connected = False
        self.sock.close()

    def is_valid_packet(self, magic_cookie, message_type):
        """
        Validates the values of the received magic_cookie, message_type from the server with the correct ones
        :param magic_cookie: the value received from the server
        :param message_type: the value received from the server
        :return: whether both the magic_cookie and the message type are correct
        """
        is_valid_cookie = magic_cookie == self.magic_cookie
        is_valid_type = message_type == self.message_type
        return is_valid_cookie and is_valid_type

    def get_server_broadcast(self):
        """
        Wait until the client is receiving a message from a server
        If received correct message then validate its message and save the server properties
        :return: the server's address and port from valid server
        """
        while self.connected:
            data, server_address = socket.recvfrom(BUFFER_SIZE)
            magic_cookie, message_type, server_port = unpack('IcH', data)
            if not self.is_valid_packet(magic_cookie, message_type):
                continue
            print(f"Received offer from {server_address}, attempting to connect...")
            return server_address, server_port

    def connect_server(self, server_address, server_port):
        """
        Connect to server using TCP socket, and play a game
        :param server_address: the host's ip address
        :param server_port: the host's port number
        """
        with socket(AF_INET, SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((server_address, server_port))
            send_data = self.team_name + "\n"
            tcp_socket.sendall(send_data.encode())
            welcome_message = tcp_socket.recv(1024).decode()
            print(welcome_message)
            answer = getch.getch()
            tcp_socket.sendall(answer.encode())
            summary_message = tcp_socket.recv(1024).decode()
            print(summary_message)

    def run(self):
        """
        Start the run of the Client
        """
        print("Client started, listening for offer requests...")
        while True:
            self.open_udp_socket()
            server_address, server_port = self.get_server_broadcast()
            self.close_socket()
            self.connect_server(server_address, server_port)
            print("Server disconnected, listening for offer requests...")
