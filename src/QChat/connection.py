import socket
import threading
from QChat.log import QChatLogger
from QChat.messages import HEADER_LENGTH, PAYLOAD_SIZE, MAX_SENDER_LENGTH, MessageFactory
from cqc.pythonLib import CQCConnection


class ConnectionError(Exception):
    pass


class DaemonThread(threading.Thread):
    """
    Thread class that defaults to running the thread with a daemon so that the thread can exit
    properly
    """
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class QChatConnection:
    def __init__(self, name, config):
        """
        Initialize a connection to the CQC server and
        :param name:   Name of the host (Must be one available by SimulaQron CQC)
        :param config: Configuration for the connection
        """
        # Lock on the connection
        self.lock = threading.Lock()

        # Logger
        self.logger = QChatLogger(__name__)

        # CQC and listening socket
        self.cqc = None
        self.listening_socket = None
        self.cqc = CQCConnection(name=name)

        # Host name the connection belongs to
        self.name = name

        # Listening configuration
        self.host = config['host']
        self.port = config['port']

        # Inbound message queue
        self.message_queue = []

        # Daemon threads
        self.listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.classical_thread = DaemonThread(target=self.listen_for_classical)

    def __del__(self):
        if self.cqc:
            self.cqc.close()
        if self.listening_socket:
            self.listening_socket.close()

    def get_connection_info(self):
        info = {
            "connection": {
                "host": self.host,
                "port": self.port
            }
        }
        return info

    def listen_for_classical(self):
        """
        A daemon for handling incoming connections.
        :return: None
        """
        self.listening_socket.bind((self.host, self.port))
        while True:
            self.logger.debug("Listening for incoming connection")
            self.listening_socket.listen(1)
            conn, addr = self.listening_socket.accept()
            self.logger.debug("Got connection from {}".format(addr))
            self.start_handler(conn, addr)

    def start_handler(self, conn, addr):
        """
        Simple connection handler that passes work to thread
        :param conn: Connection information from socket
        :param addr: Address information from socket
        :return: None
        """
        t = threading.Thread(target=self._handle_connection, args=(conn, addr))
        t.start()

    def _handle_connection(self, conn, addr):
        """
        Receives incoming QChat Messages and verifies their structure before storing them
        so that they can be retrieved.
        :param conn: Connection information from sockets
        :param addr: Address information from sockets
        :return: None
        """
        # Verify the header structure
        header = conn.recv(HEADER_LENGTH)
        if header not in MessageFactory().message_mapping.keys():
            raise ConnectionError("Incorrect message header")

        # Verify the sender structe
        padded_sender = conn.recv(MAX_SENDER_LENGTH)
        if len(padded_sender) != MAX_SENDER_LENGTH:
            raise ConnectionError("Incorrect sender length")

        # Verify the sender info
        sender = str(padded_sender.replace(b'\x00', b''), 'utf-8')
        if len(sender) == 0:
            raise ConnectionError("Invalid sender")

        # Get the message size
        size = conn.recv(PAYLOAD_SIZE)
        if len(size) != PAYLOAD_SIZE:
            raise ConnectionError("Incorrect payload size")

        # Retrieve the message data
        data_length = int.from_bytes(size, 'big')
        message_data = b''
        while len(message_data) < data_length:
            data = conn.recv(1024)
            if not data:
                raise ConnectionError("Message data too short")
            message_data += data

        # Verify the length of the sent data
        if len(message_data) > data_length or conn.recv(1):
            raise ConnectionError("Message data too long")

        # Pass the message up
        self.logger.debug("Inserting message into queue")
        m = MessageFactory().create_message(header, sender, message_data)
        self._append_message_to_queue(m)
        conn.close()

    def _append_message_to_queue(self, message):
        with self.lock:
            self.message_queue.append(message)

    def _pop_message_from_queue(self):
        with self.lock:
            return self.message_queue.pop(0)

    def recv_message(self):
        """
        Method that returns the oldest message in the queue
        :return: None
        """
        return self._pop_message_from_queue() if self.message_queue else None

    def send_message(self, host, port, message):
        """
        Connects and sends a message to the specified host:port
        :param host: Hostname to send to
        :param port: Port to send to
        :param message: Bytes object message
        :return: None
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(message)
        s.close()
        self.logger.debug("Sent message to {}:{}".format(host, port))
