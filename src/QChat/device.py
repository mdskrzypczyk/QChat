import time
from QChat.messages import RQQBMessage


class MeasurementDevice:
    def __init__(self, connection, relay_info):
        """
        Used to implement trusted/untrusted measurement devices for use in receiving BB84 states from source
        and performing measurements on the qubits
        :param connection:
        :param relay_info:
        """
        self.connection = connection

        # Connection information to the server providing the EPR pairs
        self.relay_host = relay_info["host"]
        self.relay_port = relay_info["port"]

    def requestEPR(self, user):
        """
        Method used for sending a request for EPR pairs from the source
        :param user: The user we want to share an EPR pair with
        :return: None
        """
        m = RQQBMessage(sender=self.connection.name, message_data={"user": user})
        self.connection.send_message(host=self.relay_host, port=self.relay_port, message=m.encode_message())


class LeadDevice(MeasurementDevice):
    """
    Implements measurements and EPR retrieval for a protocol leader
    """
    def measure(self, q, basis):
        if basis == 0:
            return q.measure()
        elif basis == 1:
            q.H()
            return q.measure()

    def receiveEPR(self, timeout=60):
        """
        Receives an EPR half and handles timeout
        :param timeout: The length in seconds to wait before timing out
        :return: The received qubit
        """
        start = time.time()
        while time.time() - start < timeout:
            try:
                # The leader will be responsible for requesting distribution from the source, so here we
                # follow CQC's implementation and use recvEPR to obtain the qubit
                q = self.connection.cqc.recvEPR()
                return q
            except:
                pass
        raise Exception("Timed out waiting for EPR")


class FollowDevice(MeasurementDevice):
    """
    Implements measurements and EPR retrieval for a protocol follower
    """
    def measure(self, q, basis):
        if basis == 0:
            q.rot_Y(240)
            return q.measure()
        elif basis == 1:
            q.rot_Y(208)
            return q.measure()
        elif basis == 2:
            return q.measure()

    def receiveEPR(self, timeout=60):
        """
        Receives an EPR half and handles timeout
        :param timeout: The length in seconds to wait before timing out
        :return: The received qubit
        """
        start = time.time()
        while time.time() - start < timeout:
            try:
                # As the follower we will be getting our qubit via a sendQubit call so we need
                # to use the appropriate CQC command to retrieve it
                q = self.connection.cqc.recvQubit()
                return q
            except:
                pass
        raise Exception("Timed out waiting for EPR")