import socket
import threading
from QChat.messages import HEADER_LENGTH, PAYLOAD_SIZE, Message
from SimulaQron.cqc.pythonLib.cqc import *

class QChatConnection:
    def __init__(self, name, config):
        self.cqc = CQCConnection(name)
        self.host = config['host']
        self.server_port = config['server_port']
        self.client_port = config['client_port']
        self.message_lock = threading.Lock()
        self.message_queue = []

    def listen_for_connection(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((self.host, self.server_port))
        while True:
            s.listen(1)
            conn, addr = s.accept()

            # Thread this
            self._handle_connection(conn, addr)

    def _handle_connection(self, conn, addr):
        header = conn.recv(HEADER_LENGTH)
        if header != Message.header:
            raise Exception("Incorrect message header")

        size = conn.recv(PAYLOAD_SIZE)
        if len(size) != PAYLOAD_SIZE:
            raise Exception("Incorrect payload size")

        padded_sender = conn.recv(MAX_LENGTH_SENDER)


        data_length = int.from_bytes(size, 'big')
        if data_length <= 0:
            raise Exception("Incorrect data length")

        message_data = None
        while len(message_data) < data_length:
            data = conn.recv(1024)
            if not data:
                raise Exception("Message data too short")
            message_data += data

        if len(message_data) > data_length or conn.recv(1):
            raise Exception("Message data too long")

        self._insert_into_queue(addr, Message(message_data))

    def _insert_message_into_queue(self, addr, message):
        self.message_lock.acquire()
        self.message_queue.append(message)
        self.message_lock.release()

    def get_message(self):
        return self.message_queue.pop(0)

    def send_message(self, host, port):
        pass

    def send_qubit(self, user):
        pass
