from socket import *
from struct import *
import getch
from multiprocessing import Process
from Painter import *

BUFFER_SIZE = 1024
MAX_TIMEOUT = 20


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
    udp_sock : socket
        represent the udp socket of the client
    tcp_sock : socket
        represent the tcp socket of the client
    """

    def __init__(self, team_name, port, magic_cookie, message_type):
        self.team_name = team_name
        self.port = port
        self.magic_cookie = magic_cookie
        self.message_type = message_type
        self.udp_sock = None
        self.tcp_sock = None

    def open_udp_socket(self):
        """
        Open a udp socket for the client
        """
        try:
            self.udp_sock = socket(AF_INET, SOCK_DGRAM)
            self.udp_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.udp_sock.bind(("", self.port))
        except error:
            self.close_socket(self.udp_sock)
            print(FAIL_message("Failed to open a UDP socket"))

    def open_tcp_socket(self):
        """
        Open a tcp socket for the client
        """
        try:
            self.tcp_sock = socket(AF_INET, SOCK_STREAM)
            self.tcp_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.tcp_sock.bind(("", self.port))
        except error:
            self.close_socket(self.tcp_sock)
            print(FAIL_message("Failed to open a TCP socket"))

    @staticmethod
    def close_socket(sock):
        """
        Close given socket of the client
        """
        if sock:
            sock.close()

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
        while True:
            data, server_address = self.udp_sock.recvfrom(BUFFER_SIZE)
            server_host = server_address[0]
            try:
                magic_cookie, message_type, server_port = unpack('IbH', data)
            except Exception:
                print(FAIL_message("Received packet with wrong format"))
                continue
            if not self.is_valid_packet(magic_cookie, message_type):
                print(FAIL_message("One of the packet's credentials is not valid, Skipping"))
                continue
            print(WARNING_message(f"Received offer from {server_host}, attempting to connect..."))
            return server_host, server_port

    def connect_server(self, server_address, server_port):
        """
        Connect to server using TCP socket, and play a game
        :param server_address: the host's ip address
        :param server_port: the host's port number
        """
        old_timeout = self.tcp_sock.gettimeout()
        self.tcp_sock.settimeout(5)
        try:
            try:
                self.tcp_sock.connect((server_address, server_port))
                print(OK_message("Connection Succeeded"))
                self.tcp_sock.settimeout(old_timeout)
            except error:
                self.tcp_sock.settimeout(old_timeout)
                self.close_socket(self.tcp_sock)
                return False
        except Exception:
            return False
        return True

    def communicate_server(self):
        """
        Send the server his team name and receive welcome message
        """
        send_data = self.team_name + "\n"
        self.tcp_sock.sendall(send_data.encode())
        old_timeout = self.tcp_sock.gettimeout()
        self.tcp_sock.settimeout(MAX_TIMEOUT)
        try:
            try:
                welcome_message = self.tcp_sock.recv(BUFFER_SIZE).decode()
                print(SERVER_message(welcome_message))
                self.tcp_sock.settimeout(old_timeout)
            except error:
                self.tcp_sock.settimeout(old_timeout)
                print(FAIL_message(f"Connection Timeout, received no data for {MAX_TIMEOUT} seconds"))
                return False
        except Exception:
            return False
        return True

    def send_answer(self):
        """
        Wait for an input from the client
        """
        answer = getch.getch()
        self.tcp_sock.sendall(answer.encode())

    def listen_for_server_answer(self):
        """
        Wait for server summary message
        """
        self.tcp_sock.settimeout(MAX_TIMEOUT)
        try:
            summary_message = self.tcp_sock.recv(BUFFER_SIZE).decode()
            print(SERVER_message(summary_message))
        except Exception:
            print(FAIL_message(f"Connection Timeout, received no data for {MAX_TIMEOUT} seconds"))
            pass

    def run(self):
        """
        Start the run of the Client
        """
        print(OK_message("Client started, listening for offer requests..."))
        while True:
            self.open_udp_socket()
            server_address, server_port = self.get_server_broadcast()
            self.close_socket(self.udp_sock)
            self.open_tcp_socket()
            connection_succeeded = self.connect_server(server_address, server_port)
            if connection_succeeded:
                if self.communicate_server():
                    p_input = Process(target=self.send_answer)
                    p_input.start()
                    self.listen_for_server_answer()
                    p_input.terminate()
            self.close_socket(self.tcp_sock)
            print(FAIL_message("Server disconnected, listening for offer requests...\n"))


if __name__ == '__main__':
    client = Client(team_name="THE THREAD KILLERS", port=1337, magic_cookie=0xabcddcba,
                    message_type=0x2)
    client.run()
