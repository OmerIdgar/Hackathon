from socket import *
from struct import *
import time
from scapy.all import get_if_addr
from threading import Thread, Lock
from random import randint, choice
from Painter import *
from select import select

BUFFER_SIZE = 1024
MAX_CONNECTIONS = 2
IP_BROADCAST = "255.255.255.255"


class Server:
    def __init__(self, team_name, udp_port, tcp_port, magic_cookie, message_type, destination_port):
        self.team_name = team_name
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.ip = get_if_addr("eth1")
        self.magic_cookie = magic_cookie
        self.message_type = message_type
        self.destination_port = destination_port
        self.total_clients = 0
        self.first_client = None
        self.second_client = None
        self.udp_sock = None
        self.tcp_sock = None
        self.mutex = Lock()
        self.answer = -1
        self.responder = None

    def open_udp_socket(self):
        try:
            self.udp_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
            self.udp_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.udp_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.udp_sock.bind(('', self.udp_port))
        except error:
            self.close_socket(self.udp_sock)
            print(FAIL_message("Failed to open a UDP socket"))

    def open_tcp_socket(self):
        try:
            self.tcp_sock = socket(AF_INET, SOCK_STREAM)
            self.tcp_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.tcp_sock.bind(('', self.tcp_port))
        except error:
            self.close_socket(self.tcp_sock)
            print(FAIL_message("Failed to open a TCP socket"))

    def close_socket(self, sock):
        """
        Close given socket of the client
        """
        if sock:
            sock.close()

    def send_offers(self, offer):
        """
        Send offers using broadcast
        :param offer: The offer packet
        """
        self.open_udp_socket()
        while self.total_clients < MAX_CONNECTIONS:
            self.udp_sock.sendto(offer, (IP_BROADCAST, self.destination_port))
            time.sleep(1)
        self.close_socket(self.udp_sock)


    @staticmethod
    def generate_equation():
        """
        Generate an Equation
        """
        op = choice(["+", "-", "*"])
        if op == "+":
            a = randint(0, 9)
            b = randint(0, 9 - a)
            answer = a + b
        if op == "-":
            a = randint(0, 100)
            b = randint(max(a - 10 + 1, 0), a)
            answer = a - b
        if op == "*":
            a = randint(0,4)
            if a == 0:
                b = randint(0, 100)
            elif a == 1:
                b = randint(1,9)
            elif a == 2:
                b = randint(1,4)
            elif a == 3:
                b = randint(1,3)
            elif a == 4:
                b = randint(1,2)
            answer = a * b
        return a, op, b, str(answer)


    def is_valid_client(self, client):
        """
        Check whether the client sent his team name and add save his credentials
        :param client: client socket and address
        """
        client_socket, client_address = client
        old_timeout = client_socket.gettimeout()
        client_socket.settimeout(10)
        try:
            team_name = client_socket.recv(BUFFER_SIZE).decode()
            self.mutex.acquire(True)
            if self.first_client is None:
                self.first_client = (client, team_name)
            elif self.second_client is None:
                self.second_client = (client, team_name)
            self.total_clients += 1
            print(SERVER_message(f"New Client Connected: {team_name}"))
            self.mutex.release()
            client_socket.settimeout(old_timeout)
        except Exception:
            print(FAIL_message("Client did not send his team name"))
            client_socket.settimeout(old_timeout)
            self.close_socket(client_socket)

    def listen_to_two_players(self):
        """
        Listen on tcp socket until two clients has connected
        """
        self.tcp_sock.listen() # MAX_CONNECTIONS
        while self.total_clients < MAX_CONNECTIONS:
            client = self.tcp_sock.accept()
            # thread_validate_client = Thread(target=self.is_valid_client, args=(client,))
            # thread_validate_client.start()
            self.is_valid_client(client)
        self.close_socket(self.udp_sock)

    def start_game(self):
        """
        Run the game for both clients
        """
        a, op, b, answer = self.generate_equation()
        (first_client_socket, first_client_address), first_team_name = self.first_client
        (second_client_socket, second_client_address), second_team_name = self.second_client
        welcome_message = f"Welcome to Quick Maths.\n" \
                          f"Player 1: {first_team_name}\n" \
                          f"Player 2: {second_team_name}\n" \
                          f"==\n" \
                          f"Please answer the following question as fast as you can:\n" \
                          f"How much is {a}{op}{b}?"

        clients = [first_client_socket, second_client_socket]
        for sock in clients:
            sock.sendall(welcome_message.encode())

        answered, writers, errors = select(clients, [], [], 10)

        for sock in answered:
            sock_answer = sock.recv(BUFFER_SIZE).decode()
            if sock_answer == answer:
                if sock == first_client_socket:
                    self.responder = first_team_name
                    self.answer = sock_answer
                elif sock == second_client_socket:
                    self.responder = second_team_name
                    self.answer = sock_answer
                break

        summary_message = f"Game Over!\n" \
                          f"The correct answer was {answer}!\n\n"

        if self.answer == -1:
            summary_message += "The game ended with a Draw!"
        elif self.answer == answer:
            summary_message += f"Congratulations to the winner: {self.responder}"

        first_client_socket.sendall(summary_message.encode())
        second_client_socket.sendall(summary_message.encode())
        print(SERVER_message("Game over, sending out offer requests..."))
        self.close_socket(self.tcp_sock)
        first_client_socket.close()
        second_client_socket.close()

    def restore_values(self):
        """
        Restore the values of the responders and the clients
        """
        self.total_clients = 0
        self.first_client = None
        self.second_client = None
        self.answer = -1
        self.responder = None

    def run(self):
        """
        Start the run of the Client
        """
        print(OK_message(f"Server started, listening on IP address {self.ip}"))
        offer = pack('IbH', self.magic_cookie, self.message_type, self.tcp_port)
        while True:
            self.open_tcp_socket()
            offer_thread = Thread(target=self.send_offers, name='Thread_Offers', args=(offer,))
            offer_thread.start()
            self.listen_to_two_players()
            time.sleep(10)
            self.start_game()
            self.restore_values()


if __name__ == '__main__':
    server = Server(team_name="THE THREAD KILLERS", udp_port=12345, tcp_port=11111, magic_cookie=0xabcddcba,
                    message_type=0x2, destination_port=1337)
    server.run()
