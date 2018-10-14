import time
from collections import defaultdict
from functools import partial
from queue import Queue
from QChat.core import QChatCore, DaemonThread, GLOBAL_SLEEP_TIME
from QChat.cryptobox import QChatCipher
from QChat.mailbox import QChatMailbox
from QChat.messages import QCHTMessage, GETUMessage, PUTUMessage, PTCLMessage
from QChat.protocols import ProtocolFactory, QChatKeyProtocol, QChatMessageProtocol, BB84_Purified, \
                            DIQKD, SuperDenseCoding, LEADER_ROLE, FOLLOW_ROLE


class QChatClient(QChatCore):
    def __init__(self, name, configFile=None, cqcFile=None, allow_invalid_signatures=False):
        """
        Initializes a QChat Server that serves as the primary communication interface with other applications
        :param name: Name of the host we want to be on the network
        :param allow_invalid_signatures: process messages with faulty signatures
        """
        # Outbound message queue
        self.outbound_queue = Queue()

        # Storage for encrypted chat messages
        self.mailbox = QChatMailbox()

        # Start our inbound/outbound message handlers
        self.message_sender = DaemonThread(target=self.send_outbound_messages)

        # Mapping of message headers to their appropriate handlers
        self.proc_map = {
            QCHTMessage.header: self.mailbox.storeMessage,
            GETUMessage.header: partial(self._pass_message_data, handler=self.sendUserInfo),
            PUTUMessage.header: partial(self._pass_message_data, handler=self.addUserInfo),
            PTCLMessage.header: self._follow_protocol
        }

        super(QChatClient, self).__init__(name=name, configFile=configFile, cqcFile=cqcFile,
                                          allow_invalid_signatures=allow_invalid_signatures)

    def send_outbound_messages(self):
        """
        Method for daemon thread, empties the outbound queue
        :return: None
        """
        while not time.sleep(GLOBAL_SLEEP_TIME):
            while not self.outbound_queue.empty():
                user, message = self.outbound_queue.get()
                self.sendMessage(user, message)

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
            key = p.execute()
            self.userDB.changeUserInfo(message.sender, message_key=key)

        # Exchange a message with our peer
        elif isinstance(p, QChatMessageProtocol):
            self.logger.debug("Received SuperDense coded message from {}: {}".format(message.sender,
                                                                                     p.receive_message()))

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
            key = p.execute()
            self.userDB.changeUserInfo(user, message_key=key)

        else:
            raise Exception("No known user {}".format(user))

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

    def getMessageHistory(self):
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

        return dict(messages)
