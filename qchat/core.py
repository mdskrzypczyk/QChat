import threading
import time
import json
import os
from collections import defaultdict
from qchat.connection import QChatConnection
from qchat.cryptobox import QChatSigner, QChatVerifier
from qchat.db import UserDB
from qchat.log import QChatLogger
from qchat.messages import GETUMessage, PUTUMessage, RGSTMessage

GLOBAL_SLEEP_TIME = 0.001


class DaemonThread(threading.Thread):
    """
    Helper class that starts a thread in Daemon mode so that it can close properly when the server closes
    """
    def __init__(self, target):
        super().__init__(target=target, daemon=True)
        self.start()


class QChatCore:
    def __init__(self, name, cqc_connection, configFile=None, allow_invalid_signatures=False):
        """
        Initializes a QChat Server that serves as the primary communication interface with other applications
        :param name: str
            Name of the host we want to be on the network
        :param cqc_connection: `~cqc.pythonLib.CQCConnection`
            Classical Quantum Combiner Connection used for quantum communications
        :param configFile: str
            Path to the configuration file that contains settings for the specified name
        :param allow_invalid_signatures: bool
            Process messages with faulty signatures
        """
        self.name = name
        self.logger = QChatLogger(__name__)
        self.configFile = configFile

        # This is the server's personal config
        self.config = self._load_server_config(self.name)

        # This is information for the root registry server
        self.root_config = self._load_server_config(self.config.get("root"))

        # RSA Signer for handling unauthenticated classical channels
        self.signer = QChatSigner()

        self._allow_invalid_signatures = allow_invalid_signatures

        # Connection to other applications
        self.connection = QChatConnection(name=name, cqc_connection=cqc_connection, config=self.config)

        # Storage of user/network information
        self.userDB = UserDB()

        # Load ourselves into our DB
        self.userDB.addUser(user=self.name, pub=self.signer.get_pub(), **self.connection.get_connection_info())

        # Start our inbound/outbound message handlers
        self.message_processor = DaemonThread(target=self.read_from_connection)

        # Register with the root registry
        self._register_with_root_server()

        # Storage of distributed qubit information
        self.qubit_history = defaultdict(list)

        # Inbound control messages for protocols
        self.control_message_queue = defaultdict(list)

    def _load_server_config(self, name):
        """
        Obtains the hosts server configuration from the config file
        :param name: str
            Key in configuration where settings should be loaded from
        :return: dict
            The configuration loaded from the file
        """
        if self.configFile:
            config_path = self.configFile

        else:
            path = os.path.abspath(__file__)
            config_path = os.path.dirname(path) + "/config.json"

        self.logger.debug("Loading server config for {}".format(name))

        with open(config_path) as f:
            base_config = json.load(f)
            config = base_config.get(name)
            self.logger.debug("Config: {}".format(config))

        return config

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
                self.sendRegistration(host=root_host, port=root_port)

        except Exception:
            self.logger.info("Failed to register with root server, is it running?")

    def read_from_connection(self):
        """
        Processes inbound messages from the application connection
        :return: None
        """
        while not time.sleep(GLOBAL_SLEEP_TIME):
            message = self.connection.recv_message()
            if message:
                self.start_process_thread(message)

    def start_process_thread(self, message):
        """
        Forks off a thread for handling messages so that they can be processed in parallel
        :param message: `~qchat.messages.Message`
            The message we obtained from the application connection
        :return: None
        """
        t = threading.Thread(target=self.process_message, args=(message,))
        t.start()

    def process_message(self, message):
        """
        The primary message handling entrypoint, performs signature verification/stripping before passing the
        message to a specific handler
        :param message: `~qchat.messages.Message`
            The inbound message from the application connection
        :return: None
        """
        self.logger.debug("Processing {} message from {}: {}".format(message.header, message.sender, message.data))

        # Verify the signature on the message for key message types
        if message.verify:
            if not self.userDB.hasUser(message.sender):
                self.requestUserInfo(message.sender)

            message, signature = self._strip_signature(message)
            if not self._allow_invalid_signatures:
                self._verify_message(message, signature)
            else:
                self.logger.warning("Will not verify message signature")

        # Strip unnecessary signature information should it not be necessary for the message type
        elif message.strip:
            message, _ = self._strip_signature(message)

        handler = self.proc_map.get(message.header, self._store_control_message)
        handler(message)

        self.logger.debug("Completed processing message")

    def _sign_message(self, message):
        """
        Internal method for signing outbound messages to assure authentication
        :param message: `~qchat.messages.Message`
            The message to be signed
        :return: `~qchat.messages.Message`
            The message with a signature attached
        """
        sig = self.signer.sign(message.encode_message())
        message.data["sig"] = sig.decode("ISO-8859-1")
        return message

    def _strip_signature(self, message):
        """
        Internal method for stripping signature data from a message that is unecessary to message handlers
        :param message: `~qchat.messages.Message`
            The message we want to strip
        :return: tuple
            A tuple of the message without the signature data, signature
        """
        signature = message.data.pop("sig").encode("ISO-8859-1")
        return message, signature

    def _verify_message(self, message, signature):
        """
        Internal method for verifying the signature provided with a message
        :param message: `~qchat.messages.Message`
            The message we want to verify
        :param signature: bytes
            The signature we want to verify
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
        :param message: `~qchat.messages.Message`
            The message to unpack arguments from
        :param handler: func
            The handler that will process the message
        :return: None
        """
        handler(**message.data)

    def _store_control_message(self, message):
        """
        Internal method for handling messages that do not have specific handlers
        :param message: `~qchat.messages.Message`
            The message to store
        :return: None
        """
        self.control_message_queue[message.sender].append(message)
        self.logger.debug("Stored message into control queue")

    def _get_registration_data(self):
        """
        Internal method for constructing this server's registration data
        :return: dict
            The constructed registration data
        """
        reg_data = {
            "user": self.name,
            "pub": self.getPublicKey().decode("ISO-8859-1")
        }
        reg_data.update(self.connection.get_connection_info())

        self.logger.debug("Constructing registration data: {}".format(reg_data))

        return reg_data

    def hasUser(self, user):
        """
        Interface to the user database for checking if a user exists
        :param user: str
            The name of the user to check in the database
        :return: bool
            Whether user exists or not
        """
        return self.userDB.hasUser(user)

    def addUserInfo(self, user, **kwargs):
        """
        Adds arbitrary information to the user database for a user
        :param user: str
            The user we want to add to the database
        :param kwargs: dict
            The key=value pairs we want to store in the database
        :return: None
        """
        if user == "*":
            self.logger.debug("Get bulk user info!")
            for info in kwargs["info"]:
                user_name = info.pop("user")
                if not self.userDB.hasUser(user_name):
                    self.logger.debug("Adding to user {} info {}".format(user_name, info))
                    self.userDB.addUser(user_name, **info)

        else:
            self.logger.debug("Adding to user {} info {}".format(user, kwargs))
            self.userDB.addUser(user, **kwargs)

    def getPublicInfo(self, user):
        """
        Returns the relevant public information for the application that is necessary for establishing
        RSA authenticated classical communication
        :param user: str
            The user we want the public information for
        :return: dict
            A dictionary containing the user's name, host/port info, and public key
        """
        pub_info = dict(self.userDB.getPublicUserInfo(user))
        return pub_info

    def getPublicKey(self):
        """
        Returns the server's public key
        :return: bytes
            Public key of the server
        """
        return self.userDB.getPublicKey(user=self.name)

    def getConnectionInfo(self, user):
        """
        Returns the connection information for the specified user
        :param user: str
            User we want connection information for
        :return: dict
            A dictionary containing the host/port information of the user
        """
        return self.userDB.getConnectionInfo(user)

    def sendRegistration(self, host, port):
        """
        Sends this server's registration to the specified host/port
        :param host: str
            Host of the registry
        :param port: int
            Port of the registry
        :return: None
        """
        message = RGSTMessage(sender=self.name, message_data=self._get_registration_data())
        self.connection.send_message(host, port, message.encode_message())
        self.logger.debug("Sent registration to {}:{}".format(host, port))

    def requestUserInfo(self, user):
        """
        Requests the specified user's information from the root registry in the network
        :param user: str
            User we want to obtain information for
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
        if user != "*":
            wait_start = time.time()
            while not self.userDB.hasUser(user):
                if time.time() - wait_start > 10:
                    raise Exception("Failed to get {} info from registry".format(user))

    def sendUserInfo(self, user, connection):
        """
        Sends the specified user's information to the server specified by connection
        :param user: str
            The user we want to provide information for
        :param connection: dict
            The host/port information of the receiving server
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
        :param user: str
            The user to send the message to
        :param message: `~qchat.messages.Message`
            The Message object we want to send
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
