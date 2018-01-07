import threading
import random
from Crypto.PublicKey import RSA, DSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256


class QChatServer:
    def __init__(self):
        self.connection_lock = threading.Lock()
        self.connection = QChatConnection()
        self.userDB = {}
        self.messageDB = {}
        self.initialize_mailbox()

    def initialize_mailbox(self):
        # Thread QChatConnection.listen_for_connections


    def hasUser(self, user):
        return self.userDB.get(user) != None

    def addUser(self, user, connection_info):
        self.userDB[user] = connection_info

    def registerUser(self, user, host, port, public_key):
        if self.hasUser(user):
            raise Exception("User {} already registered".format(user))
        else:
            connection_info = {"host": host, "port": port, "pub": public_key}
            self.addUser(user, connection_info)

    def getUserInfo(self, user):
        return {user, self.userDB[user]}

    def pushMessages(self, user):
        connection_info = self.userDB[user]
        for message in self.messageDB[user]:
            self.connection_lock.acquire()
            self.connection.send_classical(connection_info['host'], connection_info['port'], message)
            self.connection_lock.release()

    def getMessages(self):
        pass

    def verifyUser(self, user):
        auth = bytes([random.randint(0,255) for _ in range(128)])
        connection_info = self.userDB[user]
        self.connection_lock.acquire()
        self.connection.send_classical(connection_info['host'], connection_info['port'], auth)
        self.connection_lock.release()
        # Receive the response
        signature = ...

        pubkey = self.userDB[user]["pub"]
        rsakey = RSA.importKey(pubkey)
        signer = PKCS1_v1_5.new(rsakey)
        digest = SHA256.new()
        digest.update(auth)

        if signer.verify(digest, signature):
            return True
        return False

