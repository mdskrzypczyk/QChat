import threading
import time
import json
import os
from collections import defaultdict
from QChat.connection import QChatConnection
from QChat.cryptobox import QChatCipher, QChatSigner, QChatVerifier
from QChat.db import UserDB
from QChat.log import QChatLogger
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
        self.logger = QChatLogger(__name__)
        self.config = self._load_server_config(self.name)
        self.root_config = self._load_server_config(self.config.get("root"))
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
            root_host = self.root_config["host"]
            root_port = self.root_config["port"]
            if self.config["host"] == root_host and self.config["port"] == root_port:
                self.logger.debug("Am root server")
            else:
                self.logger.debug("Sending registration to {}:{}".format(root_host, root_port))
                self.sendRegistration(host=root_host, port=root_port)
        except:
            self.logger.info("Failed to register with root server, is it running?")

    def _load_server_config(self, name):
        path = os.path.abspath(__file__)
        config_path = os.path.dirname(path) + "/config.json"
        self.logger.debug("Loading server config {}".format(config_path))
        with open(config_path) as f:
            base_config = json.load(f)
            self.logger.debug("Config: {}".format(base_config))
        return base_config.get(name)

    def read_from_connection(self):
        self.logger.debug("Processing incoming messages")
        while True:
            message = self.connection.recv_message()
            if message:
                self.start_process_thread(message)

    def start_process_thread(self, message):
        t = threading.Thread(target=self.process_message, args=(message,))
        t.start()

    def process_message(self, message):
        self.logger.debug("Processing {} message from {}: {}".format(message.header, message.sender, message.data))
        if message.header == QCHTMessage.header:
            self.mailbox.storeMessage(message)
            self.logger.info("New QChat message from {}".format(message.sender))

        elif message.header == RGSTMessage.header:
            self.registerUser(**message.data)
            self.logger.info("Registered new contact {}".format(message.sender))

        elif message.header == GETUMessage.header:
            self.sendUserInfo(**message.data)
            self.logger.debug("Sent {} user info to {}".format(message.data["user"], message.sender))

        elif message.header == PUTUMessage.header:
            self.addUserInfo(**message.data)
            self.logger.info("Got {} user info".format(message.data["user"]))

        elif message.header == PTCLMessage.header:
            if not self.userDB.hasUser(message.sender):
                self.requestUserInfo(message.sender)
            self._follow_protocol(message)

        else:
            self.control_message_queue[message.sender].append(message)

        self.logger.debug("Completed processing message")

    def _follow_protocol(self, message):
        peer_info = {
            "user": message.sender,
        }
        peer_info.update(self.getConnectionInfo(message.sender))
        self.logger.debug("Following protocol with peer info: {}".format(peer_info))

        protocol_class = ProtocolFactory().createProtocol(name=message.data['name'])
        p = protocol_class(peer_info, self.connection, message.data['n'], self.control_message_queue[message.sender],
                           FOLLOW_ROLE)

        if isinstance(p, QChatKeyProtocol):
            self.logger.debug("Establishing key with {}".format(message.sender))
            self.userDB.changeUserInfo(message.sender, message_key=p.execute())

    def _wait_for_control_message(self, header, user):
        self.logger.debug("Waiting for control message")
        while self.control_message_queue[user] == []:
            time.sleep(1)
        cm = self.control_message_queue[user].pop(0)
        if cm.header != header:
            raise Exception("Bad control message")

        return cm

    def _get_registration_data(self):
        reg_data = {
            "user": self.name,
            "pub": str(self.getPublicKey(), 'utf-8')
        }
        reg_data.update(self.connection.get_connection_info())
        self.logger.debug("Constructing registration data: {}".format(reg_data))
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
        self.logger.debug("Adding to user {} info {}".format(user, kwargs))
        self.userDB.addUser(user, **kwargs)

    def registerUser(self, user, connection, pub):
        if self.userDB.hasUser(user):
            raise Exception("User {} already registered".format(user))
        else:
            self.addUserInfo(user, pub=bytes(pub, 'utf-8'), connection=connection)

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

    def sendUserInfo(self, user, connection):
        self.logger.debug("Sending {} info to {}".format(user, connection))
        message = PUTUMessage(sender=self.name, message_data=self.getPublicInfo(user))
        self._send_message(connection["host"], connection["port"], message)

    def requestUserInfo(self, user):
        request_message_data = {
            "user": user,
        }
        request_message_data.update(self.connection.get_connection_info())
        m = GETUMessage(sender=self.name, message_data=request_message_data)
        self.connection.send_message(self.root_config["host"], self.root_config["port"], m.encode_message())

        wait_start = time.time()
        while not self.userDB.hasUser(user):
            if time.time() - wait_start > 2:
                raise Exception("Failed to get {} info from registry".format(user))

    def getMailboxMessage(self, user):
        return self.mailbox.getMessage(user)

    def sendMessage(self, user, message):
        if not self.userDB.hasUser(user):
            self.requestUserInfo(user)

        connection_info = self.userDB.getConnectionInfo(user)
        host = connection_info['host']
        port = connection_info['port']
        self.connection.send_message(host, port, message.encode_message())

    def createQChatMessage(self, user, plaintext):
        user_key = self.userDB.getMessageKey(user)
        if not user_key:
            self._establish_key(user, 100)
            user_key=self.userDB.getMessageKey(user)
        nonce, ciphertext, tag = QChatCipher(user_key).encrypt(bytes(plaintext, 'utf-8'))
        message_data = {
            "nonce": nonce.decode("ISO-8859-1"),
            "ciphertext": ciphertext.decode("ISO-8859-1"),
            "tag": tag.decode("ISO-8859-1")
        }
        message = QCHTMessage(sender=self.name, message_data=message_data)
        return message

    def sendQChatMessage(self, user, plaintext):
        if not self.userDB.hasUser(user):
            self.requestUserInfo(user)

        message = self.createQChatMessage(user, plaintext)
        self.sendMessage(user, message)

    def get_message_history(self, user, count):
        messages = []
        for _ in range(count):
            qm = self.mailbox.getMessage(user)
            if qm.sender != user:
                raise Exception("Mailbox for {} contained message from {}".format(user, qm.sender))
            else:
                user_key = self.userDB.getMessageKey(user)
                nonce = qm.data['nonce'].encode("ISO-8859-1")
                ciphertext = qm.data['ciphertext'].encode("ISO-8859-1")
                tag = qm.data['tag'].encode("ISO-8859-1")
                message = QChatCipher(user_key).decrypt((nonce, ciphertext, tag))
                message.decode("ISO-8859-1")
                messages.append(message)

        return messages

