import threading
import time
import json
import os
import random
from collections import defaultdict
from functools import partial
from queue import Queue
from QChat.connection import QChatConnection
from QChat.cryptobox import QChatCipher, QChatSigner, QChatVerifier
from QChat.db import UserDB
from QChat.log import QChatLogger
from QChat.mailbox import QChatMailbox
from QChat.messages import GETUMessage, PTCLMessage, PUTUMessage, RGSTMessage, QCHTMessage, RQQBMessage
from QChat.protocols import ProtocolFactory, QChatKeyProtocol, QChatMessageProtocol, BB84_Purified, \
                            DIQKD, SuperDenseCoding, LEADER_ROLE, FOLLOW_ROLE

class DaemonThread(threading.Thread):
    """
    Helper class that starts a thread in Daemon mode so that it can close properly when the server closes
    """
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class QChatClient:
    def __init__(self, name, cqcFilePath=None):
        """
        Initializes a QChat Server that serves as the primary communication interface with other applications
        :param name: Name of the host we want to be on the network
        """
        self.name=name
        self.logger = QChatLogger(__name__)

        # This is the server's personal config
        self.config = self._load_server_config(self.name)

        # This is information for the root registry server
        self.root_config = self._load_server_config(self.config.get("root"))

        # Connection to other applications
        self.connection = QChatConnection(name=name, config=self.config, cqcFilePath=cqcFilePath)

        # Inbound control messages for protocols
        self.control_message_queue = defaultdict(list)

        # Outbound message queue
        self.outbound_queue = Queue()

        # Storage for encrypted chat messages
        self.mailbox = QChatMailbox()

        # RSA Signer for handling unauthenticated classical channels
        self.signer = QChatSigner()

        # Storage of user/network information
        self.userDB = UserDB()

        # Load ourselves into our DB
        self.userDB.addUser(user=self.name, pub=self.signer.get_pub(), **self.connection.get_connection_info())

        # Storage of distributed qubit information
        self.qubit_history = defaultdict(list)

        # Start our inbound/outbound message handlers
        self.message_processor = DaemonThread(target=self.read_from_connection)
        self.message_sender = DaemonThread(target=self.send_outbound_messages)

        # Register with the root registry
        self._register_with_root_server()

    def _load_server_config(self, name):
        """
        Obtains the hosts server configuration from the config file
        :param name:
        :return:
        """
        path = os.path.abspath(__file__)
        config_path = os.path.dirname(path) + "/config.json"
        self.logger.debug("Loading server config {}".format(config_path))

        with open(config_path) as f:
            base_config = json.load(f)
            self.logger.debug("Config: {}".format(base_config))

        return base_config.get(name)

    def _register_with_root_server(self):
        """
        Registers our application server with the root registry server
        :return: None
        """
        try:
            root_host = self.root_config["host"]
            root_port = self.root_config["port"]

            # No need to register with ourselves if we are the root registry
            if self.config["host"] == root_host and self.config["port"] == root_port:
                self.logger.debug("Am root server")
            else:
                self.logger.debug("Sending registration to {}:{}".format(root_host, root_port))
                self.sendRegistration(host=root_host, port=root_port)
        except:
            self.logger.info("Failed to register with root server, is it running?")

    def send_outbound_messages(self):
        """
        Method for daemon thread, empties the outbound queue
        :return: None
        """
        while True:
            if not self.outbound_queue.empty():
                user, message = self.outbound_queue.get()
                self.sendMessage(user, message)

    def read_from_connection(self):
        """
        Processes inbound messages from the application connection
        :return: None
        """
        while True:
            message = self.connection.recv_message()
            if message:
                self.start_process_thread(message)

    def start_process_thread(self, message):
        """
        Forks off a thread for handling messages so that they can be processed in parallel
        :param message: The message we obtained from the application connection
        :return: None
        """
        t = threading.Thread(target=self.process_message, args=(message,))
        t.start()

    def process_message(self, message):
        """
        The primary message handling entrypoint, performs signature verification/stripping before passing the
        message to a specific handler
        :param message: The inbound message from the application connection
        :return: None
        """
        self.logger.debug("Processing {} message from {}: {}".format(message.header,
                                                                     message.sender,
                                                                     message.data))

        # Verify the signature on the message for key message types
        if message.verify:
            if not self.userDB.hasUser(message.sender):
                self.requestUserInfo(message.sender)

            message, signature = self._strip_signature(message)
            self._verify_message(message, signature)

        # Strip unnecessary signature information should it not be necessary for the message type
        elif message.strip:
            message, _ = self._strip_signature(message)

        # Mapping of message headers to their appropriate handlers
        proc_map = {
            QCHTMessage.header: self.mailbox.storeMessage,
            GETUMessage.header: partial(self._pass_message_data, handler=self.sendUserInfo),
            PUTUMessage.header: partial(self._pass_message_data, handler=self.addUserInfo),
            PTCLMessage.header: self._follow_protocol
        }

        handler = proc_map.get(message.header, self._store_control_message)
        handler(message)
        self.logger.debug("Completed processing message")

    def _sign_message(self, message):
        """
        Internal method for signing outbound messages to assure authentication
        :param message:
        :return:
        """
        sig = self.signer.sign(message.encode_message())
        message.data["sig"] = sig.decode("ISO-8859-1")
        return message

    def _strip_signature(self, message):
        """
        Internal method for stripping signature data from a message that is unecessary to message handlers
        :param message: The message we want to strip
        :return: A tuple of the message, signature
        """
        signature = message.data.pop("sig").encode("ISO-8859-1")
        return message, signature

    def _verify_message(self, message, signature):
        """
        Internal method for verifying the signature provided with a message
        :param message:   The message we want to verify
        :param signature: The signature we want to verify
        :return: None
        """
        data = message.encode_message()

        # Use the stored public key for verification
        pub = self.userDB.getPublicKey(message.sender)

        if not QChatVerifier(pub).verify(data, signature):
            raise Exception("Obtained message with incorrect signature")

        self.logger.debug("Successfully verified signature")

    def _pass_message_data(self, message, handler):
        """
        Internal method for passing the message data as arguments to the message handlers
        :param message: The message to unpack arguments from
        :param handler: The handler that will process the message
        :return: None
        """
        handler(**message.data)

    def _follow_protocol(self, message):
        """
        Internal method for handling a PTCL Message, upon receipt of a PTCL Message the server assumes the
        follower role in the protocol
        :param message: The PTCL Message containing protocol initialization information
        :return: None
        """
        # Construct peer information for the protocol
        peer_info = {
            "user": message.sender,
        }
        peer_info.update(self.getConnectionInfo(message.sender))

        # Construct the protocol object
        protocol_class = ProtocolFactory().createProtocol(name=message.data.pop('name'))
        self.logger.debug("Following {} protocol with user {}".format(protocol_class.name, message.sender))

        p = protocol_class(**message.data, peer_info=peer_info, connection=self.connection,
                           ctrl_msg_q=self.control_message_queue[message.sender],
                           outbound_q=self.outbound_queue, role=FOLLOW_ROLE, relay_info=self.root_config)

        # Establish a key with our peer
        if isinstance(p, QChatKeyProtocol):
            # key = p.execute()
            key = b'\x00'*16
            self.userDB.changeUserInfo(message.sender, message_key=key)

        # Exchange a message with our peer
        elif isinstance(p, QChatMessageProtocol):
            self.logger.debug("Received SuperDense coded message from {}: {}".format(message.sender,
                                                                                     p.receive_message()))

    def _store_control_message(self, message):
        """
        Internal method for handling messages that do not have specific handlers
        :param message: The message to store
        :return: None
        """
        self.control_message_queue[message.sender].append(message)
        self.logger.debug("Stored message into control queue")

    def _get_registration_data(self):
        """
        Internal method for constructing this server's registration data
        :return: The constructed registration data
        """
        reg_data = {
            "user": self.name,
            "pub": self.getPublicKey().decode("ISO-8859-1")
        }
        reg_data.update(self.connection.get_connection_info())

        self.logger.debug("Constructing registration data: {}".format(reg_data))

        return reg_data

    def _establish_key(self, user, key_size, protocol_class=BB84_Purified):
        """
        Internal method for leading a key establishment protocol
        :param user: The user we want to establish the shared key with
        :param key_size: The size of the key (in bytes) that we want to construct
        :param protocol_class: The protocol we want to use to establish the key
        :return: None
        """
        # Check that we have the user in out system
        if self.hasUser(user):
            # Construct peer info for the protocol
            peer_info = {
                "user": user,
            }
            peer_info.update(self.getConnectionInfo(user))

            # Construct the protocol object
            p = protocol_class(peer_info=peer_info, connection=self.connection, key_size=key_size,
                               ctrl_msg_q=self.control_message_queue[user], outbound_q=self.outbound_queue,
                               role=LEADER_ROLE, relay_info=self.root_config)

            # Execute the protocol and store the derived key in the user database
            # key = p.execute()
            key = b'\x00'*16
            self.userDB.changeUserInfo(user, message_key=key)

        else:
            raise Exception("No known user {}".format(user))

    def hasUser(self, user):
        """
        Interface to the user database for checking if a user exists
        :param user:
        :return:
        """
        return self.userDB.hasUser(user)

    def addUserInfo(self, user, **kwargs):
        """
        Adds arbitrary information to the user database for a user
        :param user: The user we want to add to the database
        :param kwargs: The key=value pairs we want to store in the database
        :return: None
        """
        if user == "*":
            self.logger.debug("Get bulk user info!")
            for info in kwargs["info"]:
                user_name = info.pop("user")
                self.logger.debug("Adding to user {} info {}".format(user_name, info))
                self.userDB.addUser(user, **info)

        else:
            self.logger.debug("Adding to user {} info {}".format(user, kwargs))
            self.userDB.addUser(user, **kwargs)

    def getPublicInfo(self, user):
        """
        Returns the relevant public information for the application that is necessary for establishing
        RSA authenticated classical communication
        :param user: The user we want the public information for
        :return: A dictionary containing the user's name, host/port info, and public key
        """
        pub_info = dict(self.userDB.getPublicUserInfo(user))
        return pub_info

    def getPublicKey(self):
        """
        Returns the server's public key
        :return:
        """
        return self.userDB.getPublicKey(user=self.name)

    def getConnectionInfo(self, user):
        """
        Returns the connection information for the specified user
        :param user: User we want connection information for
        :return: A dictionary containing the host/port information of the user
        """
        return self.userDB.getConnectionInfo(user)

    def sendRegistration(self, host, port):
        """
        Sends this server's registration to the specified host/port
        :param host: Host of the registry
        :param port: Port of the registry
        :return: None
        """
        message = RGSTMessage(sender=self.name, message_data=self._get_registration_data())
        self.connection.send_message(host, port, message.encode_message())
        self.logger.info("Sent registration to {}:{}".format(host, port))

    def requestUserInfo(self, user):
        """
        Requests the specified user's information from the root registry in the network
        :param user: User we want to obtain information for
        :return: None
        """
        # Construct the request message
        request_message_data = {
            "user": user,
        }
        request_message_data.update(self.connection.get_connection_info())

        # Create the messag eobject and sign it
        m = GETUMessage(sender=self.name, message_data=request_message_data)
        m = self._sign_message(m)

        # Send the request to the root registry
        self.connection.send_message(self.root_config["host"], self.root_config["port"], m.encode_message())

        # Wait for a response from the root registry
        wait_start = time.time()
        while not self.userDB.hasUser(user):
            if time.time() - wait_start > 10:
                raise Exception("Failed to get {} info from registry".format(user))

    def sendUserInfo(self, user, connection):
        """
        Sends the specified user's information to the server specified by connection
        :param user: The user we want to provide information for
        :param connection: The host/port information of the receiving server
        :return: None
        """
        self.logger.debug("Sending {} info to {}".format(user, connection))

        # Construct and sign the message containing the requested information
        message = PUTUMessage(sender=self.name, message_data=self.getPublicInfo(user))
        message = self._sign_message(message)
        self.connection.send_message(host=connection["host"], port=connection["port"], message=message.encode_message())

    def sendMessage(self, user, message):
        """
        Interface for sending a preconstructed message object to a user
        :param user: The user to send the message to
        :param message: The Message object we want to send
        :return: None
        """
        # Ensure we know how to contact the user, if not resolve the information
        if not self.userDB.hasUser(user):
            self.requestUserInfo(user)

        # Get the connection information
        connection_info = self.userDB.getConnectionInfo(user)
        host = connection_info['host']
        port = connection_info['port']

        # Sign the message and send it via the connection
        message = self._sign_message(message)
        self.connection.send_message(host, port, message.encode_message())

    def createQChatMessage(self, user, plaintext):
        """
        Creates an encrypted chat message
        :param user: The user we want to create the message for
        :param plaintext: The string we want to communicate via the message
        :return: An encrypted QChat message object
        """
        # Check that we have a message key established with this user and establish one if none
        user_key = self.userDB.getMessageKey(user)
        if not user_key:
            self._establish_key(user, 16)
            user_key=self.userDB.getMessageKey(user)

        # Encrypt the plaintext information
        nonce, ciphertext, tag = QChatCipher(user_key).encrypt(plaintext.encode("ISO-8859-1"))

        # Construct the QChat Message data
        message_data = {
            "nonce": nonce.decode("ISO-8859-1"),
            "ciphertext": ciphertext.decode("ISO-8859-1"),
            "tag": tag.decode("ISO-8859-1")
        }
        message = QCHTMessage(sender=self.name, message_data=message_data)
        self.logger.debug("Created QChat message")
        return message

    def sendQChatMessage(self, user, plaintext):
        """
        Sends a QChat Message containing the plaintext information to the specified user
        :param user: The user we wish to send the message to
        :param plaintext: The plaintext information to communicate to the user
        :return: None
        """
        # Ensure we have a route to the user
        if not self.userDB.hasUser(user):
            self.requestUserInfo(user)

        # Create message object
        message = self.createQChatMessage(user, plaintext)
        self.sendMessage(user, message)
        self.logger.info("Sent QChat message to {}".format(user))

    def sendSuperdenseMessage(self, user, plaintext):
        """
        Sends a superdense coded message to the specified user
        :param user: The user we want to send the superdense message to
        :param plaintext: The plaintext we wish to communicate
        :return: None
        """
        # Get user information if we don't have it
        if not self.userDB.hasUser(user):
            self.requestUserInfo(user)

        # Construct peer info for the protocol
        peer_info = {
            "user": user,
        }
        peer_info.update(self.getConnectionInfo(user))

        # Prepare the protocol
        p = SuperDenseCoding(peer_info=peer_info, connection=self.connection,
                             ctrl_msg_q=self.control_message_queue[user], outbound_q=self.outbound_queue,
                             role=LEADER_ROLE, relay_info=self.root_config)

        # Send the message using the protocol
        p.send_message(plaintext.encode("ISO-8859-1"))
        self.logger.info("Sent superdense message to {}".format(user))

    def getMessageHistory(self, user):
        """
        Returns the received message history stored in our mailbox for the specified user
        :param user: The user to get message history for
        :return: A list of decrypted messages that we have received from the user
        """
        messages = defaultdict(list)
        for _, qm in enumerate(self.mailbox.popMessages()):
            sender = qm.sender
            user_key = self.userDB.getMessageKey(sender)
            # Obtain cipher data
            nonce = qm.data['nonce'].encode("ISO-8859-1")
            ciphertext = qm.data['ciphertext'].encode("ISO-8859-1")
            tag = qm.data['tag'].encode("ISO-8859-1")

            # Decrypt the essage
            message = QChatCipher(user_key).decrypt((nonce, ciphertext, tag))
            message.decode("ISO-8859-1")
            messages[sender].append(message)

        return messages