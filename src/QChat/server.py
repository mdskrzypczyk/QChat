import threading
import random
import time
from collections import defaultdict
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
from QChat.connection import QChatConnection
from QChat.messages import GETUMessage, RQTUMessage, RGSTMessage, QCHTMessage


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class QChatServer:
    def __init__(self, name, config):
        self.name=name
        self.rsa_key = RSA.generate(2048)
        self.pub_key = self.rsa_key.publickey().exportKey()
        self.connection_lock = threading.Lock()
        self.connection = QChatConnection(name=name, config=config)
        self.userDB = {}
        self.control_messages = defaultdict(list)
        self.mailbox = defaultdict(list)
        self.initialize_mailbox()

    def process_message(self, message):
        if message.header == QCHTMessage.header:
            self.mailbox[message.sender].append(message)

        elif message.header == RGSTMessage.header:
            self.registerUser(**message.data)

        elif message.header == RQTUMessage.header:
            self.sendUserInfo(**message.data)

        elif message.header == GETUMessage.header:
            self.addUserInfo(**message.data)

        else:
            self.control_messages[message.sender].append(message)

    def wait_for_control_message(self, header, user):
        while self.control_messages[user] == []:
            time.sleep(1)
        cm = self.control_messages[user].pop(0)
        if cm.header != header:
            raise Exception("Bad control message")

        return cm

    def load_mailbox(self):
        while True:
            time.sleep(1)
            message = self.connection.get_message()
            if message:
                self.process_message(message)

    def initialize_mailbox(self):
        self.listener = DaemonThread(target=self.connection.listen_for_connection)
        self.message_reader = DaemonThread(target=self.load_mailbox)

    def hasUser(self, user):
        return self.userDB.get(user) != None

    def addUserInfo(self, user, host, port, pub):
        self.userDB[user] = {
            "host": host,
            "port": port,
            "pub": pub
        }

    def registerUser(self, user, host, port, pub):
        if self.hasUser(user):
            raise Exception("User {} already registered".format(user))
        else:
            self.addUserInfo(user, host, port, bytes(pub, 'utf-8'))

    def sendRegistration(self, host, port):
        message_data = {
            "user": self.name,
            "host": self.connection.host,
            "port": self.connection.port,
            "pub": str(self.pub_key, 'utf-8'),
        }
        message = RGSTMessage(sender=self.name, message_data=message_data)
        self.connection.send_message(host, port, message.encode_message())

    def getUserInfo(self, user):
        connection_info = dict(self.userDB[user])
        connection_info["user"] = user
        return connection_info

    def sendUserInfo(self, user, host, port):
        user_info = self.getUserInfo(user)
        user_info["pub"] = str(user_info["pub"], 'utf-8')
        m = GETUMessage(sender=self.name, message_data=user_info)
        self.connection.send_message(host=host, port=port, message=m.encode_message())

    def requestUserInfo(self, user, host, port):
        request_message_data = {
            "user": user,
            "host": self.connection.host,
            "port": self.connection.port
        }
        m = RQTUMessage(sender=self.name, message_data=request_message_data)
        self.connection.send_message(host, port, m.encode_message())

    def pushMessages(self, user):
        connection_info = self.userDB[user]
        for message in self.messageDB[user]:
            self.connection_lock.acquire()
            self.connection.send_classical(connection_info['host'], connection_info['port'], message)
            self.connection_lock.release()

    def getMailboxMessage(self, user):
        if self.mailbox[user]:
            return self.mailbox[user].pop(0)

    def sendMessage(self, user, message):
        if user not in self.userDB.keys():
            raise Exception("No known route to {}".format(user))
        connection_info = self.userDB[user]
        host = connection_info['host']
        port = connection_info['port']
        self.connection.send_message(host, port, message.encode_message())

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

    def establish_key(self, protocol):
        protocol.execute()

