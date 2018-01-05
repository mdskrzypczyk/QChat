from connection import QChatConnection
from db import UserDB, MessageDB
from Crypto.PublicKey import RSA, DSA

class QChatClient:
    def __init__(self):
        self.connection = QChatConnection()
        self.userDB = UserDB()
        self.messageDB = MessageDB()
        self.server_info = ServerInfo()

    def _connect_to_server(self):
        self.connection.connect_to_server(self.server_info)

    def _connect_to_client(self):
        pass

    def _get_client_info(self):
        pass

    def register_user(self):
        pass

    def send_message(self):
        pass

    def read_message(self):
        pass
