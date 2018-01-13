import socket
import threading
from QChat.log import QChatLogger
from QChat.messages import HEADER_LENGTH, PAYLOAD_SIZE, MAX_SENDER_LENGTH, MessageFactory
from SimulaQron.cqc.pythonLib.cqc import *


class ConnectionError(Exception):
    pass


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()

class QChatConnection:
    def __init__(self, name, config):
        self.lock = threading.Lock()
        self.logger = QChatLogger(__name__)
        self.cqc = None
        self.listening_socket = None
        self.cqc = CQCConnection(name)
        self.name = name
        self.host = config['host']
        self.port = config['port']
        self.message_queue = []
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.thread = DaemonThread(target=self.listen)

    def __del__(self):
        if self.cqc:
            self.cqc.close()
        if self.listening_socket:
            self.listening_socket.close()

    def get_connection_info(self):
        info = {
            "host": self.host,
            "port": self.port
        }
        return info

    def listen(self):
        self.listening_socket.bind((self.host, self.port))
        while True:
            self.logger.debug("Listening for incoming connection")
            self.listening_socket.listen(1)
            conn, addr = self.listening_socket.accept()
            self.logger.debug("Got connection from {}".format(addr))

            # Thread this
            t = threading.Thread(target=self._handle_connection, args=(conn, addr))
            t.start()

    def _handle_connection(self, conn, addr):
        header = conn.recv(HEADER_LENGTH)
        if header not in MessageFactory().message_mapping.keys():
            raise ConnectionError("Incorrect message header")

        padded_sender = conn.recv(MAX_SENDER_LENGTH)
        if len(padded_sender) != MAX_SENDER_LENGTH:
            raise ConnectionError("Incorrect sender length")

        sender = str(padded_sender.replace(b'\x00', b''), 'utf-8')
        if len(sender) == 0:
            raise ConnectionError("Invalid sender")

        size = conn.recv(PAYLOAD_SIZE)
        if len(size) != PAYLOAD_SIZE:
            raise ConnectionError("Incorrect payload size")

        data_length = int.from_bytes(size, 'big')
        message_data = b''
        while len(message_data) < data_length:
            data = conn.recv(1024)
            if not data:
                raise ConnectionError("Message data too short")
            message_data += data

        if len(message_data) > data_length or conn.recv(1):
            raise ConnectionError("Message data too long")

        self.logger.debug("Inserting message into queue")
        self._append_message_to_queue(MessageFactory().create_message(header, sender, message_data))
        conn.close()

    def _append_message_to_queue(self, message):
        with self.lock:
            self.message_queue.append(message)

    def _pop_message_from_queue(self):
        with self.lock:
            return self.message_queue.pop(0)

    def recv_message(self):
        return self._pop_message_from_queue() if self.message_queue else None

    def send_message(self, host, port, message):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(message)
        s.close()
        self.logger.debug("Sent message to {}:{}".format(host, port))

    def send_qubit(self, user):
        pass
