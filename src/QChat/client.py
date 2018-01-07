from connection import QChatConnection
from QChat.server import QChatServer
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA, DSA

class QChatClient(QChatServer):
    def __init__(self):
        self.rsa_key = RSA.generate(2048)
        self.pub_key = self.key.publickey().exportKey()
        self.connection = QChatConnection()
        self.userDB = {}
        self.messageDB = {}
        self.server_info = ServerInfo()

    def _get_client_info(self):
        # Send a request to the server for the user connection information

    def authenticateUser(self):
        # Receive the authentication string
        auth = ...
        digest = SHA256.new()
        digest.update(auth)
        signer = PKCS1_v1_5(self.rsa_key)
        sig = signer.sign(digest)

        # Send the signature to the server

        # Verify that authentication was successful


    def register_user(self):
        # Send a message requesting registration for a username
        # Send host, port, public key information for receiving messages
        # Verify that registration was successful

    def send_qubit(self, user):
        # Send qubit over the cqc connection to the user

    def send_message(self, user):
        # Check if we have the user's information
        # Obtain it from the server if we do not
        # Send a message to the user's client

    def read_message(self, user):
        # Check inbox of messages from user
        # Read the oldest message in this inbox
