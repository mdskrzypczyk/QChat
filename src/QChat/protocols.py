import random
import time
from QChat.ecc import ECC_Golay
from QChat.log import QChatLogger
from QChat.messages import PTCLMessage, BB84Message

LEADER_ROLE = 0
FOLLOW_ROLE = 1
IDLE_TIMEOUT = 2


class ProtocolException(Exception):
    pass


class QChatProtocol:
    def __init__(self, peer_info, connection, n, ctrl_msg_q, outbound_q, role):
        self.logger = QChatLogger(__name__)
        self.connection = connection
        self.n = n
        self.ctrl_msg_q = ctrl_msg_q
        self.outbound_q = outbound_q
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

    def _wait_for_control_message(self, idle_timeout=IDLE_TIMEOUT, message_type=None):
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
        self.outbound_q.put(message)
        # self.connection.send_message(host=self.peer_info["host"], port=self.peer_info["port"],
        #                              message=message.encode_message())

    def exchange_messages(self, message_data, message_type):
        if self.role == LEADER_ROLE:
            self._send_control_message(message_data=message_data, message_type=message_type)
            return self._wait_for_control_message(message_type=message_type)
        else:
            m = self._wait_for_control_message(message_type=message_type)
            self._send_control_message(message_data=message_data, message_type=message_type)
            return m


class QChatKeyProtocol(QChatProtocol):
    pass

class QChatMessageProtocol(QChatProtocol):
    pass

class BB84_Purified(QChatKeyProtocol):
    name = "BB84_PURIFIED"

    def _lead_protocol(self):
        self._send_control_message(message_data={"name": self.name, "n": self.n}, message_type=PTCLMessage)
        response = self._wait_for_control_message(message_type=BB84Message)
        if response.data["ACK"] != "ACK":
            raise ProtocolException("Failed to establish leader/role")


    def _follow_protocol(self):
        self._send_control_message(message_data={"ACK": "ACK"}, message_type=BB84Message)

    def _distribute_bb84_states(self, eavesdropper=None):
        x = []
        theta = []
        while len(x) < self.n:
            if eavesdropper:
                q = self.connection.cqc.createEPR(eavesdropper)
            else:
                q = self.connection.cqc.createEPR(self.peer_info["user"])

            basisflip = random.randint(0, 1)
            if basisflip:
                q.H()

            x.append(q.measure())
            theta.append(basisflip)

            ack = self._wait_for_control_message(message_type=BB84Message)
            if ack.data["ack"] != True:
                raise ProtocolException("Error distributing BB84 states")

        return x, theta

    def _receive_bb84_states(self):
        x = []
        theta = []
        while len(x) < self.n:
            q = self.connection.cqc.recvEPR()
            basisflip = random.randint(0, 1)
            if basisflip:
                q.H()

            theta.append(basisflip)
            x.append(q.measure())

            self._send_control_message(message_data={"ack": True}, message_type=BB84Message)
        return x, theta

    def _filter_theta(self, x, theta):
        x_remain = []
        response = self.exchange_messages(message_data={"theta": theta}, message_type=BB84Message)
        theta_hat = response.data["theta"]
        for bit, basis, basis_hat in zip(x, theta, theta_hat):
            if basis == basis_hat:
                x_remain.append(bit)

        return x_remain

    def _estimate_error_rate(self, x, num_test_bits):
        test_bits = []
        test_indices = []

        if self.role == LEADER_ROLE:
            while len(test_indices) < num_test_bits and len(x) > 0:
                index = random.randint(0, len(x) - 1)
                test_bits.append(x.pop(index))
                test_indices.append(index)

            self._send_control_message(message_data={"test_indices": test_indices}, message_type=BB84Message)
            response = self._wait_for_control_message(message_type=BB84Message)
            target_test_bits = response.data["test_bits"]
            self._send_control_message(message_data={"test_bits": test_bits}, message_type=BB84Message)
            m = self._wait_for_control_message(message_type=BB84Message)
            if not m.data["ack"]:
                raise ProtocolException("Failed to distribute test information")

        elif self.role == FOLLOW_ROLE:
            m = self._wait_for_control_message(message_type=BB84Message)
            test_indices = m.data["test_indices"]
            for index in test_indices:
                test_bits.append(x.pop(index))

            self._send_control_message(message_data={"test_bits": test_bits}, message_type=BB84Message)
            m = self._wait_for_control_message(message_type=BB84Message)
            target_test_bits = m.data["test_bits"]
            self._send_control_message(message_data={"ack": True}, message_type=BB84Message)


        num_error = 0
        for t1, t2 in zip(test_bits, target_test_bits):
            if t1 != t2:
                num_error += 1

        return (num_error / num_test_bits)

    def _reconcile_information(self, x, ecc=ECC_Golay()):
        """
        Information Reconciliation
        :param x: Set of codewords
        :return: Bytestring of reconciled information
        """
        reconciled = []
        for codeword in ecc.chunk(x):
            if len(codeword) < ecc.codeword_length:
                return codeword, reconciled
            if self.role == LEADER_ROLE:
                s = ecc.encode(codeword)
                self._send_control_message(message_data={"s": s}, message_type=BB84Message)
                reconciled += codeword
                m = self._wait_for_control_message(message_type=BB84Message)
                if not m.data["ack"]:
                    raise ProtocolException("Failed to reconcile secrets")
            elif self.role == FOLLOW_ROLE:
                m = self._wait_for_control_message(message_type=BB84Message)
                s = m.data["s"]
                reconciled += ecc.decode(codeword, s)
                self._send_control_message(message_data={"ack": True}, message_type=BB84Message)

        return [], reconciled

    def _amplify_privacy(self, X):
        """
        One-round privacy amplification sourced from https://eprint.iacr.org/2010/456.pdf
        :param X: A bytestring of the information we wish to distill
        :return: Privacy amplified byte from X
        """
        if self.role == LEADER_ROLE:
            Y = random.randint(0, 2 ** 8 - 1)
            temp = (Y * X[0]).to_bytes(2, 'big')
            R = temp[0]
            T = temp[1] + X[1]
            self._send_control_message(message_data={"Y": Y, "T": T}, message_type=BB84Message)
            m = self._wait_for_control_message(message_type=BB84Message)
            if not m.data["ack"]:
                return None

        elif self.role == FOLLOW_ROLE:
            m = self._wait_for_control_message(message_type=BB84Message)
            Y = m.data["Y"]
            T = m.data["T"]
            temp = (Y * X[0]).to_bytes(2, 'big')
            if T != X[1] + temp[1]:
                self._send_control_message(message_data={"ack": False}, message_type=BB84Message)
                return None
            R = temp[0]
            self._send_control_message(message_data={"ack": True}, message_type=BB84Message)

        return R.to_bytes(1, 'big')

    def _execute(self):
        key = b''
        while len(key) < self.n:
            if self.role == LEADER_ROLE:
                x, theta = self._distribute_bb84_states()
            else:
                x, theta = self._receive_bb84_states()

            x_remain = self._filter_theta(x=x, theta=theta)

            num_test_bits = self.n // 4
            error_rate = self._estimate_error_rate(x_remain, num_test_bits)

            if error_rate > 0.5:
                raise RuntimeError("Error rate of {}, aborting protocol".format(error_rate))

            x_remain = x_remain[:-(len(x_remain) % 16)]
            reconciled = self._reconcile_information(x_remain)

            key += self._amplify_privacy(reconciled)

        return key

    def distill_tested_data(self):
        if self.role == LEADER_ROLE:
            x, theta = self._distribute_bb84_states()
        else:
            x, theta = self._receive_bb84_states()

        x_remain = self._filter_theta(x=x, theta=theta)

        num_test_bits = len(x_remain) // 2
        error_rate = self._estimate_error_rate(x_remain, num_test_bits)

        if error_rate >= 0.5:
            raise RuntimeError("Error rate of {}, aborting protocol".format(error_rate))
        return x_remain

    def execute(self):
        key = b''
        secret_bits = []
        reconciled = []
        while len(key) < 16:
            while len(reconciled) < 16:
                while len(secret_bits) < 23:
                    secret_bits += self.distill_tested_data()
                secret_bits, reconciled_bits = self._reconcile_information(secret_bits)
                reconciled += reconciled_bits
            reconciled_bytes = int(''.join([str(i) for i in reconciled[:16]]), 2).to_bytes(2, 'big')
            reconciled = reconciled[16:]
            b = self._amplify_privacy(reconciled_bytes)
            if b:
                key += b
        self.logger.debug("Derived key {}".format(key))
        return key


class SuperDenseCoding(QChatMessageProtocol):
    def _lead_protocol(self):
        pass

    def _follow_protocol(self):
        pass

    def execute(self, message):
        pass


class ProtocolFactory:
    def __init__(self):
        self.protocol_mapping = {
            BB84_Purified.name: BB84_Purified
        }

    def createProtocol(self, name):
        return self.protocol_mapping.get(name)