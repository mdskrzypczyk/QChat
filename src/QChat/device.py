import time
from QChat.messages import RQQBMessage


class MeasurementDevice:
    def __init__(self, connection, relay_info):
        self.connection = connection
        self.relay_host = relay_info["host"]
        self.relay_port = relay_info["port"]

    def requestEPR(self, user):
        m = RQQBMessage(sender=self.connection.name, message_data={"user": user})
        self.connection.send_message(host=self.relay_host, port=self.relay_port, message=m.encode_message())


class LeadDevice(MeasurementDevice):
    def measure(self, q, basis):
        if basis == 0:
            return q.measure()
        elif basis == 1:
            q.H()
            return q.measure()

    def receiveEPR(self, timeout=5):
        start = time.time()
        while time.time() - start < timeout:
            try:
                q = self.connection.cqc.recvEPR()
                return q
            except:
                pass
        raise Exception("Timed out waiting for EPR")


class FollowDevice(MeasurementDevice):
    def measure(self, q, basis):
        if basis == 0:
            q.rot_X(16)
            return q.measure()
        elif basis == 1:
            q.rot_X(48)
            return q.measure()
        elif basis == 2:
            return q.measure()

    def receiveEPR(self, timeout=5):
        start = time.time()
        while time.time() - start < timeout:
            try:
                q = self.connection.cqc.recvQubit()
                return q
            except:
                pass
        raise Exception("Timed out waiting for EPR")