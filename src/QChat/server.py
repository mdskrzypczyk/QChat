import random
from functools import partial
from QChat.messages import GETUMessage, PUTUMessage, RGSTMessage, RQQBMessage
from QChat.core import QChatCore, DaemonThread


class QChatServer(QChatCore):
    def __init__(self, name, cqcFile=None):
        """
        Initializes a QChat Server that serves as the primary communication interface with other applications
        :param name: Name of the host we want to be on the network
        """

        # Mapping of message headers to their appropriate handlers
        self.proc_map = {
            RGSTMessage.header: partial(self._pass_message_data, handler=self.registerUser),
            GETUMessage.header: partial(self._pass_message_data, handler=self.sendUserInfo),
            PUTUMessage.header: partial(self._pass_message_data, handler=self.addUserInfo),
            RQQBMessage.header: self._distribute_qubits
        }

        super(QChatServer, self).__init__(name=name, cqcFile=cqcFile)

    def _distribute_qubits(self, message):
        """
        Internal method that allows the server to act as an EPR source.  For use in modeling the Purified BB84
        protocol
        :param message: Message containing user information for EPR distribution
        :return: None
        """
        # First send half to the message sender and store the second
        self.logger.debug("Got request for EPR from {}".format(message.sender))
        q = self.connection.cqc.createEPR(message.sender)
        self.logger.debug("Sent one half of EPR to {}".format(message.sender))
        # Optionally attack the distribution, comparison should be change to control influence
        peer = message.data["user"]
        p = random.random()
        if p < 0:
            # Store our measurement and send a new qubit to the peer
            outcome = q.measure()
            self.qubit_history[peer].append(outcome)
            q = qubit(self.connection.cqc)

        # Send other half to peer
        self.connection.cqc.sendQubit(q, peer)
        self.logger.info("Shared qubits between {} and {}".format(message.sender, peer))

    def registerUser(self, user, connection, pub):
        """
        Registers a new user to our server
        :param user: The user being registered
        :param connection: Connection (host/port) information of the user
        :param pub: The RSA public key of the user for authentication
        :return: None
        """
        if self.userDB.hasUser(user):
            raise Exception("User {} already registered".format(user))
        else:
            self.addUserInfo(user, pub=pub.encode("ISO-8859-1"), connection=connection)
            self.logger.info("Registered new contact {}".format(user))
