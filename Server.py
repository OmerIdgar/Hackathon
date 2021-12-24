from socket import *
from struct import *
import sys
import time
from scapy import get_if_addr
from threading import Thread
from random import randint, choice

BUFFER_SIZE = 1024
MAX_CONNECTIONS = 2

class Server:
    def __init__(self, team_name, port, magic_cookie, message_type, send_port):
        self.team_name = team_name
        self.port = port
        self.ip = get_if_addr("eth0")
        self.magic_cookie = magic_cookie
        self.message_type = message_type
        self.send_port = send_port
        self.address = (self.ip, self.port)
        self.connected = False
        self.clients = []
        self.total_clients = 0
        self.sock = None
        # self.semaphore = Semaphore(MAX_CONNECTIONS)

    def send_to_all_clients(self, msg):
        for client in self.clients:
            client.connection.send(msg)

    def send_to_client(self, ip, port, msg):
        for client in self.clients:
            if client.ip == ip and client.port == port:
                client.connection.send(msg)

    def open_udp_socket(self):
        try:
            self.sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
            self.sock.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)
            self.sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            self.sock.bind(("", self.port))
            self.connected = True
        except error:
            self.connected = False
            if self.sock:
                self.sock.close()
            sys.exit(1)

    def open_tcp_socket(self):
        try:
            self.sock = socket(AF_INET, SOCK_STREAM)
            self.sock.bind(("", self.port))
            self.connected = True
        except error:
            self.connected = False
            if self.sock:
                self.sock.close()
            sys.exit(1)

    def send_offers(self, offer):
        while self.total_clients < 2:
            self.sock.sendto(offer, ("255.255.255.255", self.send_port))
            time.sleep(1)

    def handle_new_client(self, client_socket, addr):
        while True:
            msg = client_socket.recv(1024)
            # do some checks and if msg == someWeirdSignal: break:
            print(addr, ' >> ', msg)
            msg = raw_input('SERVER >> ')
            client_socket.send(msg)
        client_socket.close()


    def generate_equation(self):
        op = choice(["+", "-"])
        if op == "+":
            a = randint(0, 9)
            b = randint(0, a)
            answer = a + b
        if op == "-":
            a = randint(0, 100) #4
            b = randint(max(a-10+1, 0),a)
            answer = a - b
        return a, op, b, answer

    def listen_to_two_players(self):
        self.sock.listen(2)
        first_client_socket, first_client_address = self.sock.accept()
        self.total_clients += 1
        second_client_socket, second_client_address = self.sock.accept()
        self.total_clients += 1
        time.sleep(10)

        first_team_name = first_client_socket.recv(1024).decode()
        second_team_name = second_client_socket.recv(1024).decode()
        a, op, b, answer = self.generate_equation()
        welcome_message = f"Welcome to Quick Maths.\n" \
                          f"Player 1: {first_team_name}\n" \
                          f"Player 2: {second_team_name}\n" \
                          f"==\n" \
                          f"Please answer the following question as fast as you can:\n" \
                          f"How much is {a}{op}{b}?"
        first_client_socket.sendall(welcome_message.encode())
        second_client_socket.sendall(welcome_message.encode())
        start_time = time.time()
        end_time = time.time()

        first_client_socket.close()
        second_client_socket.close()

    def run(self):
        print(f"Server started, listening on IP address {self.ip}")
        self.open_udp_socket()
        # self.sock.settimeout(0.2)
        offer = pack('IcH', self.magic_cookie, self.message_type, self.port)
        while True:
            offer_thread = Thread(target=self.send_offers, name='Thread_Offers', args=offer)
            offer_thread.start()
            self.listen_to_two_players()
