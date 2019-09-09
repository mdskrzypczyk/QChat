import random
from cqc.pythonLib import qubit
from functools import partial
from qchat.messages import GETUMessage, PUTUMessage, RGSTMessage, RQQBMessage
from qchat.core import QChatCore


class QChatServer(QChatCore):
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

        # Mapping of message headers to their appropriate handlers
        self.proc_map = {
            RGSTMessage.header: partial(self._pass_message_data, handler=self.registerUser),
            GETUMessage.header: partial(self._pass_message_data, handler=self.sendUserInfo),
            PUTUMessage.header: partial(self._pass_message_data, handler=self.addUserInfo),
            RQQBMessage.header: self._distribute_qubits
        }

        super(QChatServer, self).__init__(name=name, cqc_connection=cqc_connection, configFile=configFile,
                                          allow_invalid_signatures=allow_invalid_signatures)

    def _distribute_qubits(self, message):
        """
        Internal method that allows the server to act as an EPR source.  For use in modeling the Purified BB84
        protocol
        :param message: `~qchat.messages.RQQBMessage`
            Message containing user information for EPR distribution
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
        self.logger.debug("Sent other half of EPR to {}".format(peer))
        self.logger.debug("Shared qubits between {} and {}".format(message.sender, peer))

    def registerUser(self, user, connection, pub):
        """
        Registers a new user to our server
        :param user: str
            The user being registered
        :param connection: dict
            Connection (host/port) information of the user
        :param pub: bytes
            The RSA public key of the user for authentication
        :return: None
        """
        if self.userDB.hasUser(user):
            raise Exception("User {} already registered".format(user))
        else:
            self.addUserInfo(user, pub=pub.encode("ISO-8859-1"), connection=connection)
            self.logger.info("Registered new user {}".format(user))
