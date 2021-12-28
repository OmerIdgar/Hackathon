from socket import *
from struct import *
import sys
import time
from scapy.all import get_if_addr
from threading import Thread, Lock
from random import randint, choice

BUFFER_SIZE = 1024
MAX_CONNECTIONS = 2
IP_BROADCAST = "255.255.255.255"


class Server:
    def __init__(self, team_name, port, magic_cookie, message_type, destination_port):
        self.team_name = team_name
        self.port = port
        self.ip = get_if_addr("eth1")
        self.magic_cookie = magic_cookie
        self.message_type = message_type
        self.destination_port = destination_port
        self.total_clients = 0
        self.udp_sock = None
        self.tcp_sock = None
        self.mutex = Lock
        self.answer = -1
        self.responder = None

    def open_udp_socket(self):
        try:
            self.udp_sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
            self.udp_sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.udp_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.udp_sock.bind(("", self.port))
        except error:
            self.close_socket(self.udp_sock)
            # sys.exit(1)

    def open_tcp_socket(self):
        try:
            self.tcp_sock = socket(AF_INET, SOCK_STREAM)
            self.tcp_sock.bind(("", self.port))
        except error:
            self.close_socket(self.tcp_sock)
            # sys.exit(1)

    def close_socket(self, sock):
        """
        Close given socket of the client
        """
        if sock:
            sock.close()

    def send_offers(self, offer):
        while self.total_clients < MAX_CONNECTIONS:
            self.udp_sock.sendto(offer, (IP_BROADCAST, self.destination_port))
            time.sleep(1)

    def generate_equation(self):
        op = choice(["+", "-"])
        if op == "+":
            a = randint(0, 9)
            b = randint(0, 9 - a)
            answer = a + b
        if op == "-":
            a = randint(0, 100)
            b = randint(max(a - 10 + 1, 0), a)
            answer = a - b
        return a, op, b, answer

    def start_game(self, client_socket, team_name, welcome_message):
        client_socket.sendall(welcome_message.encode())
        client_socket.settimeout(10)
        try:
            client_answer = client_socket.recv(1024).decode()
            with self.mutex:
                if self.answer != -1:
                    self.answer = client_answer
                    self.responder = team_name
        except error:
            print("Passed 10 seconds, skipping...")

    def handle_timeout(self, client1, client2):
        client1.settimeout(10)
        client2.settimeout(10)

    def restore_timeout(self, client1, client2):
        client1.settimeout(None)
        client2.settimeout(None)

    def listen_to_two_players(self):
        self.open_tcp_socket()
        self.tcp_sock.listen(MAX_CONNECTIONS)
        while self.total_clients < 2:
            client_socket, client_address = self.tcp_sock.accept()
            try:
                team_name = client_socket.recv(BUFFER_SIZE).decode()
            except Exception:
                pass

        first_client_socket, first_client_address = self.tcp_sock.accept()
        self.total_clients += 1
        second_client_socket, second_client_address = self.tcp_sock.accept()
        self.total_clients += 1
        time.sleep(10)


    def listen_to_two_players(self):
        self.open_tcp_socket()
        self.tcp_sock.listen(MAX_CONNECTIONS)
        first_client_socket, first_client_address = self.tcp_sock.accept()
        self.total_clients += 1
        second_client_socket, second_client_address = self.tcp_sock.accept()
        self.total_clients += 1
        time.sleep(10)

        self.handle_timeout(first_client_socket, second_client_socket)
        first_team_name = first_client_socket.recv(1024).decode()
        second_team_name = second_client_socket.recv(1024).decode()
        self.restore_timeout(first_client_socket, second_client_socket)

        a, op, b, answer = self.generate_equation()
        welcome_message = f"Welcome to Quick Maths.\n" \
                          f"Player 1: {first_team_name}\n" \
                          f"Player 2: {second_team_name}\n" \
                          f"==\n" \
                          f"Please answer the following question as fast as you can:\n" \
                          f"How much is {a}{op}{b}?"

        thread_client_1 = Thread(target=self.start_game, name='Thread1_game',
                                 args=(first_client_socket, first_team_name, welcome_message))
        thread_client_2 = Thread(target=self.start_game, name='Thread2_game',
                                 args=(second_client_socket, second_team_name, welcome_message))
        thread_client_1.start()
        thread_client_2.start()

        thread_client_1.join()
        thread_client_2.join()

        summary_message = f"Game Over!\n" \
                          f"The correct answer was {answer}!\n\n"

        if self.answer == -1:
            summary_message += "The game ended with a Draw!"
        elif self.answer == answer:
            summary_message += f"Congratulations to the winner: {self.responder}"

        first_client_socket.sendall(summary_message.encode())
        second_client_socket.sendall(summary_message.encode())
        print("Game over, sending out offer requests...")
        self.close_tcp_socket()
        first_client_socket.close()
        second_client_socket.close()

    def run(self):
        print(f"Server started, listening on IP address {self.ip}")
        self.open_udp_socket()
        offer = pack('IbH', self.magic_cookie, self.message_type, self.port)
        while True:
            offer_thread = Thread(target=self.send_offers, name='Thread_Offers', args=(offer,))
            offer_thread.start()
            self.listen_to_two_players()


if __name__ == '__main__':
    server = Server(team_name="omer_guy", port=12345, magic_cookie=0xabcddcba,
                    message_type=0x2, destination_port=14000)
    server.run()
