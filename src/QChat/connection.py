import socket
import threading
from SimulaQron.cqc.pythonLib.cqc import *

class QChatConnection:
    def __init__(self, name, config):
        self.cqc = CQCConnection(name)
        self.host = config['host']
        self.port = config['port']
        self.message_lock = threading.Lock()
        self.message_queue = []

    def send_classical(self, host, port, data):
        s = self.connect_to_host(host, port)
        s.sendall(data)
        response = s.recv(1024)
        s.close()

    def establish_key(self, host, port):
        # BB84 or whatever here
        pass

    def connect_to_host(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        return s

    def listen_for_connection(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.port))
        while True:
            s.listen(1)
            conn, addr = s.accept()
            self.handle_connection(conn, addr)

    def handle_connection(self, conn, addr):
        message = None
        while True:
            data = conn.recv(1024)
            if not data:
                break
            message += data

        if message:
            insert_message_into_queue(message)

    def insert_message_into_queue(self, message):
        self.message_lock.acquire()
        self.message_queue.append(message)
        self.message_lock.release()

    def recv_classical(self):
        self.message_lock.acquire()
        message = self.message_queue.pop(0)
        self.message_lock.release()
        return message