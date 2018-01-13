import threading
import time
import json
from collections import defaultdict
from QChat.connection import QChatConnection
from QChat.cryptobox import QChatCipher, QChatSigner, QChatVerifier
from QChat.db import UserDB
from QChat.mailbox import QChatMailbox
from QChat.messages import GETUMessage, PTCLMessage, PUTUMessage, RGSTMessage, QCHTMessage
from QChat.protocols import ProtocolFactory, QChatKeyProtocol, BB84_Purified, LEADER_ROLE, FOLLOW_ROLE


class DaemonThread(threading.Thread):
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class QChatServer:
    def __init__(self, name):
        self.name=name
        self.config = self._load_server_config(self.name)
        root_server_config = self._load_server_config("Root Server")
        self.root_host = root_server_config["host"]
        self.root_port = root_server_config["port"]
        self.connection = QChatConnection(name=name, config=self.config)
        self.control_message_queue = defaultdict(list)
        self.mailbox = QChatMailbox()
        self.signer = QChatSigner()
        self.userDB = UserDB()
        self.userDB.addUser(user=self.name, pub=self.signer.get_pub(), **self.connection.get_connection_info())
        self.message_processor = DaemonThread(target=self.read_from_connection)
        self._register_with_root_server()

    def _register_with_root_server(self):
        try:
            if self.config["host"] == self.root_host and self.config["port"] == self.root_port:
                print("I am root server")
            else:
                self.sendRegistration(host=self.root_host, port=self.root_port)
        except:
            print("Could not connect to root server, try later")

    def _load_server_config(self, name):
        config_path = "Qchat/config.json"
        with open(config_path) as f:
            base_config = json.load(f)
        return base_config.get(name)

    def read_from_connection(self):
        while True:
            time.sleep(0.1)
            message = self.connection.recv_message()
            if message:
                self.process_message(message)

    def process_message(self, message):
        print("Got message {}, {}, {}".format(message.header, message.sender, message.data))
        if message.header == QCHTMessage.header:
            self.mailbox.storeMessage(message)

        elif message.header == RGSTMessage.header:
            self.registerUser(**message.data)

        elif message.header == GETUMessage.header:
            self.sendUserInfo(**message.data)

        elif message.header == PUTUMessage.header:
            self.addUserInfo(**message.data)

        elif message.header == PTCLMessage.header:
            t = threading.Thread(target=self._follow_protocol, args=(message,))
            t.start()

        else:
            self.control_message_queue[message.sender].append(message)

    def _follow_protocol(self, message):
        peer_info = {
            "user": message.sender,
        }
        peer_info.update(self.getConnectionInfo(message.sender))

        protocol_class = ProtocolFactory().createProtocol(name=message.data['name'])
        p = protocol_class(peer_info, self.connection, message.data['n'], self.control_message_queue[message.sender],
                           FOLLOW_ROLE)
        if isinstance(p, QChatKeyProtocol):
            self.userDB.changeUserInfo(message.sender, message_key=p.execute())

    def _wait_for_control_message(self, header, user):
        while self.control_message_queue[user] == []:
            time.sleep(1)
        cm = self.control_message_queue[user].pop(0)
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

    def _send_message(self, host, port, message):
        self.connection.send_message(host, port, message.encode_message())

    def _establish_key(self, user, key_size, protocol_class=BB84_Purified):
        if self.hasUser(user):
            peer_info = {
                "user": user,
            }
            peer_info.update(self.getConnectionInfo(user))
            p = protocol_class(peer_info=peer_info, connection=self.connection, n=key_size,
                               ctrl_msg_q=self.control_message_queue[user], role=LEADER_ROLE)

        self.userDB.changeUserInfo(user, message_key=p.execute())

    def hasUser(self, user):
        return self.userDB.hasUser(user)

    def addUserInfo(self, user, **kwargs):
        print(user, kwargs)
        self.userDB.addUser(user, **kwargs)

    def registerUser(self, user, connection, pub):
        if self.userDB.hasUser(user):
            raise Exception("User {} already registered".format(user))
        else:
            self.addUserInfo(user, pub=bytes(pub, 'utf-8'), **connection)

    def getPublicKey(self):
        return self.userDB.getPublicKey(user=self.name)

    def getPublicInfo(self, user):
        pub_info = dict(self.userDB.getPublicUserInfo(user))
        pub_info["pub"] = str(pub_info["pub"], 'utf-8')
        pub_info["user"] = user
        return pub_info

    def sendRegistration(self, host, port):
        message = RGSTMessage(sender=self.name, message_data=self._get_registration_data())
        self._send_message(host, port, message)

    def getConnectionInfo(self, user):
        return self.userDB.getConnectionInfo(user)

    def sendUserInfo(self, user, connection_info):
        message = RGSTMessage(sender=self.name, message_data=self.getPublicInfo(user))
        self._send_message(connection_info["host"], connection_info["port"], message)

    def requestUserInfo(self, user, root=True, host=None, port=None):
        server_host = self.root_host if root else host
        server_port = self.root_port if root else port
        request_message_data = {
            "user": user,
            "connection_info": self.connection.get_connection_info()
        }
        m = GETUMessage(sender=self.name, message_data=request_message_data)
        self.connection.send_message(server_host, server_port, m.encode_message())

    def getMailboxMessage(self, user):
        return self.mailbox.getMessage(user)

    def sendMessage(self, user, message):
        if not self.userDB.hasUser(user):
            raise Exception("No known route to {}".format(user))

        connection_info = self.userDB.getConnectionInfo(user)
        host = connection_info['host']
        port = connection_info['port']
        self.connection.send_message(host, port, message.encode_message())

    def createQChatMessage(self, user, plaintext):
        user_key = self.userDB.getMessageKey(user)
        nonce, ciphertext, tag = QChatCipher(user_key).encrypt(plaintext)
        message_data = {
            "nonce": str(nonce),
            "ciphertext": str(ciphertext),
            "tag": str(tag)
        }
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
                raise Exception("Mailbox for {} contained message from {}".format(user, qm.sender))
            else:
                user_key = self.userDB[user]['key']
                nonce = qm.data['nonce']
                ciphertext = qm.data['ciphertext']
                tag = qm.data['tag']
                message = QChatCipher(user_key).decrypt((nonce, ciphertext, tag))
                messages.append(message)

        return messages

