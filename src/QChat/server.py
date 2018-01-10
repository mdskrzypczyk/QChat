import threading
import time
from collections import defaultdict
from QChat.connection import QChatConnection
from QChat.cryptobox import QChatCipher, QChatSigner, QChatVerifier
from QChat.db import UserDB
from QChat.mailbox import QChatMailbox
from QChat.messages import GETUMessage, PUTUMessage, RGSTMessage, QCHTMessage


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class QChatServer:
    def __init__(self, name, config):
        self.name=name
        self.connection = QChatConnection(name=name, config=config)
        self.control_messages = defaultdict(list)
        self.mailbox = QChatMailbox()
        self.signer = QChatSigner()
        self.userDB = UserDB()
        self.userDB.addUser(user=self.name, pub=self.signer.get_pub(), **self.connection.get_connection_info())
        self.message_processor = DaemonThread(target=self.read_from_connection)

    def read_from_connection(self):
        while True:
            time.sleep(1)
            message = self.connection.recv_message()
            if message:
                self.process_message(message)

    def process_message(self, message):
        if message.header == QCHTMessage.header:
            self.mailbox.storeMessage(message)

        elif message.header == RGSTMessage.header:
            self.registerUser(**message.data)

        elif message.header == GETUMessage.header:
            self.sendUserInfo(**message.data)

        elif message.header == PUTUMessage.header:
            self.addUserInfo(**message.data)

        else:
            self.control_messages[message.sender].append(message)

    def _wait_for_control_message(self, header, user):
        while self.control_messages[user] == []:
            time.sleep(1)
        cm = self.control_messages[user].pop(0)
        if cm.header != header:
            raise Exception("Bad control message")

        return cm

    def _get_registration_data(self):
        reg_data = {
            "user": self.name,
            "connection": {
                "host": self.connection.host,
                "port": self.connection.port
            },
            "pub": str(self.getPublicKey(), 'utf-8'),
        }
        return reg_data

    def _send_message(self, message):
        self.connection.send_message(message.encode_message())

    def hasUser(self, user):
        return self.userDB.get(user) != None

    def addUserInfo(self, user, **kwargs):
        self.userDB.addUser(user, kwargs)

    def registerUser(self, user, host, port, pub):
        if self.userDB.hasUser(user):
            raise Exception("User {} already registered".format(user))
        else:
            self.addUserInfo(user, host=host, port=port, pub=bytes(pub, 'utf-8'))

    def getPublicKey(self):
        return self.userDB.getUserKey(user=self.name)

    def getPublicInfo(self, user):
        return self.userDB.getPublicUserInfo(user)

    def sendRegistration(self, host, port):
        message = RGSTMessage(sender=self.name, message_data=self._get_registration_data())
        self._send_message(message)

    def getConnectionInfo(self, user):
        return self.userDB.getConnectionInfo(user)

    def sendUserInfo(self, user, host, port):
        m = GETUMessage(sender=self.name, message_data=self.getPublicInfo(user))
        self.connection.send_message(host=host, port=port, message=m.encode_message())

    def requestUserInfo(self, user, host, port):
        request_message_data = {
            "user": user,
            "connection_info": self.connection.get_connection_info()
        }
        m = PUTUMessage(sender=self.name, message_data=request_message_data)
        self.connection.send_message(host, port, m.encode_message())

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

    def establishKey(self, user):
        key = ...
        self.userDB[user]['key'] = key

    def createQChatMessage(self, user, plaintext):
        user_key = self.userDB.getMessageKey(user)
        nonce, ciphertext, tag = QChatCipher(user_key).encrypt(plaintext)
        message_data = {"nonce": nonce, "ciphertext": ciphertext, "tag": tag}
        message = QCHTMessage(sender=self.name, message_data=message_data)
        return message

    def sendQChatMessage(self, user, plaintext):
        if self.userDB.hasUser(user):
            message = self.createQChatMessage(user, plaintext)
            self.sendMessage(user, message)
        else:
            raise Exception("User {} does not exist on the network")

    def get_message_history(self, user, count):
        qchat_messages = self.mailbox.get_messages(user, count)
        messages = []
        for qm in qchat_messages:
            if qm.sender != user:
                raise Exception("Mailbox for {} contained message from {}".format(user, qchat_message.sender))
            else:
                user_key = self.userDB[user]['key']
                nonce = qm.data['nonce']
                ciphertext = qm.data['ciphertext']
                tag = qm.data['tag']
                message = QChatCipher(user_key).decrypt((nonce, ciphertext, tag))
                messages.append(message)

        return messages

