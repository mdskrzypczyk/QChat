import time
from qchat.core import GLOBAL_SLEEP_TIME
from qchat.messages import RQQBMessage
from qchat.log import QChatLogger


class MeasurementDevice:
    def __init__(self, connection, relay_info):
        """
        Used to implement trusted/untrusted measurement devices for use in receiving BB84 states from source
        and performing measurements on the qubits
        :param connection: `~qchat.connection.QChatConnection`
            Connection to be used for classical and quantum communications
        :param relay_info: dict
            Relay information about how messages travel over other nodes
        """
        self.connection = connection
        self.logger = QChatLogger(__name__)

        # Connection information to the server providing the EPR pairs
        self.relay_host = relay_info["host"]
        self.relay_port = relay_info["port"]

    def requestEPR(self, user):
        """
        Method used for sending a request for EPR pairs from the source
        :param user: str
            The user we want to share an EPR pair with
        :return: None
        """
        m = RQQBMessage(sender=self.connection.name, message_data={"user": user})
        self.connection.send_message(host=self.relay_host, port=self.relay_port, message=m.encode_message())


class LeadDevice(MeasurementDevice):
    """
    Implements measurements and EPR retrieval for a protocol leader
    """
    def measure(self, q, basis):
        """
        Measures a qubit in the specified basis
        :param q: `~cqc.pythonLib.qubit`
            The qubit to be measured
        :param basis: int
            0 - Z-basis, 1 - X-basis
        :return:
        """
        if basis == 0:
            return q.measure()
        elif basis == 1:
            q.H()
            return q.measure()

    def receiveEPR(self, timeout=60):
        """
        Receives an EPR half and handles timeout
        :param timeout: int
            The length in seconds to wait before timing out
        :return: `~cqc.pythonLib.qubit`
            The received qubit
        """
        start = time.time()
        while not time.sleep(GLOBAL_SLEEP_TIME) and time.time() - start < timeout:
            try:
                # The leader will be responsible for requesting distribution from the source, so here we
                # follow CQC's implementation and use recvEPR to obtain the qubit
                q = self.connection.cqc.recvEPR()
                return q
            except Exception:
                pass
        raise Exception("Timed out waiting for EPR")


class FollowDevice(MeasurementDevice):
    """
    Implements measurements and EPR retrieval for a protocol follower
    """
    def measure(self, q, basis):
        """
        Measures a qubit in the specified basis
        :param q: `~cqc.pythonLib.qubit`
            The qubit to be measured
        :param basis: int
            Selects the rotated basis to be used (primarily in DIQKD)
        :return:
        """
        if basis == 0:
            q.rot_Y(48)
            return q.measure()
        elif basis == 1:
            q.rot_Y(16)
            return q.measure()
        elif basis == 2:
            return q.measure()

    def receiveEPR(self, timeout=60):
        """
        Receives an EPR half and handles timeout
        :param timeout: int
            The length in seconds to wait before timing out
        :return: `~cqc.pythonLib.qubit`
            The received qubit
        """
        start = time.time()
        while not time.sleep(GLOBAL_SLEEP_TIME) and time.time() - start < timeout:
            try:
                # As the follower we will be getting our qubit via a sendQubit call so we need
                # to use the appropriate CQC command to retrieve it
                q = self.connection.cqc.recvQubit()
                return q
            except Exception:
                pass
        raise Exception("Timed out waiting for EPR")
