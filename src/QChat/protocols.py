import random
import time
from QChat.messages import PTCLMessage, BB84Message


class ProtocolException(Exception):
    pass


LEADER_ROLE = 0
FOLLOW_ROLE = 1
IDLE_TIMEOUT = 2

class QChatProtocol:
    def __init__(self, peer_info, connection, n, ctrl_msg_q, role):
        self.connection = connection
        self.n = n
        self.ctrl_msg_q = ctrl_msg_q
        self.peer_info = peer_info
        self.role = role
        if role == LEADER_ROLE:
            self._lead_protocol()
        elif role == FOLLOW_ROLE:
            self._follow_protocol()

    def _lead_protocol(self):
        raise NotImplementedError

    def _follow_protocol(self):
        raise NotImplementedError

    def _wait_for_control_message(self, idle_timeout=2, message_type=None):
        wait_start = time.time()
        while not self.ctrl_msg_q:
            curr_time = time.time()
            if curr_time - wait_start > idle_timeout:
                raise ProtocolException("Timed out waiting for control message")
        message = self.ctrl_msg_q.pop(0)
        if not isinstance(message, message_type):
            raise ProtocolException("Received incorrect control message")
        return message

    def _send_control_message(self, message_data, message_type):
        message = message_type(sender=self.connection.name, message_data=message_data)
        self.connection.send_message(host=self.peer_info["host"], port=self.peer_info["port"],
                                     message=message.encode_message())


class BB84_Purified(QChatProtocol):
    name = "BB84_PURIFIED"

    def _lead_protocol(self):
        self._send_control_message(message_data={"name": self.name, "n": self.n}, message_type=PTCLMessage)
        response = self._wait_for_control_message(message_type=BB84Message)
        if response.data["ACK"] != "ACK":
            raise ProtocolException("Failed to establish leader/role")


    def _follow_protocol(self):
        self._send_control_message(message_data={"ACK": "ACK"}, message_type=BB84Message)

    def _distribute_bb84_states(self, eavesdropper="Eve"):
        x = []
        theta = []
        while len(x) < self.n:
            if eavesdropper:
                q = self.connection.cqc.createEPR(eavesdropper)
            else:
                q = self.connection.cqc.createEPR(self.peer_info["user"])

            bitflip = random.randint(0, 1)
            if bitflip:
                q.X()
            basisflip = random.randint(0, 1)
            if basisflip:
                q.H()

            x.append(q.measure())
            theta.append(basisflip)

        ack = self._wait_for_control_message(idle_timeout=2, message_type=BB84Message)
        if ack.data["ack"] != True:
            raise ProtocolException("Error distributing BB84 states")

        return x, theta

    def _receive_bb84_states(self):
        x = []
        theta = []
        while len(x) < self.n:
            q = self.connection.cqc.recvQubit()
            basisflip = random.randint(0, 1)
            if basisflip:
                q.H()

            theta.append(basisflip)
            x.append(q.measure())

        self._send_control_message(message_data={"ack": True}, message_type=BB84Message)
        return x, theta

    def _filter_theta(self, x, theta):
        x_remain = []
        self._send_control_message(message_data={"theta": theta}, message_type=BB84Message)
        response = self._wait_for_control_message(idle_timeout=1, message_type=BB84Message)
        theta_hat = response.data["theta"]
        for bit, basis, basis_hat in zip(x, theta, theta_hat):
            if basis == basis_hat:
                x_remain.append(bit)

        return x_remain

    def _estimate_error_rate(self, x, num_test_bits):
        test_bits = []
        test_indices = []

        while len(test_indices) < num_test_bits and len(x) > 0:
            index = random.randint(0, len(x) - 1)
            test_bits.append(x.pop(index))
            test_indices.append(index)

        self._send_control_message(message_data={"test_indices": test_indices}, message_type=BB84Message)
        response = self._wait_for_control_message(idle_timeout=2, message_type=BB84Message)
        target_test_bits = response.data["test_bits"]
        self._send_control_message(message_data={"test_bits": test_bits}, message_type=BB84Message)
        print("Alice target_test_bits: ", target_test_bits)

        num_error = 0
        for t1, t2 in zip(test_bits, target_test_bits):
            if t1 != t2:
                num_error += 1

        return (num_error / num_test_bits)

    def _extract_key(self, x, r):
        return (sum([xj * rj for xj, rj in zip(x, r)]) % 2)

    def execute(self):
        if self.role == LEADER_ROLE:
            x, theta = self._distribute_bb84_states()
        else:
            x, theta = self._receive_bb84_states()
            m = self._wait_for_control_message(header=BB84Message.header, user=user)
        if m.data.get("message") != "States received":
            raise ProtocolException("Failed to transmit BB84 states")

        x_remain = self._filter_theta(x=x, theta=theta)

        num_test_bits = self.n // 4
        error_rate = self._estimate_error_rate(x_remain, num_test_bits)

        if error_rate > 1:
            raise RuntimeError("Error rate of {}, aborting protocol")

        r = [random.randint(0, 1) for _ in x_remain]
        self._send_control_message(message_data={"r": r}, message_type=BB84Message)
        return self._extract_key(x_remain, r)


class ProtocolFactory:
    def __init__(self):
        self.protocol_mapping = {
            BB84_Purified.name: BB84_Purified
        }

    def createProtocol(self, name):
        return self.protocol_mapping.get(name)