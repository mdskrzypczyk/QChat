import random
import time
from QChat.device import LeadDevice, FollowDevice
from QChat.ecc import ECC_Golay
from QChat.log import QChatLogger
from QChat.messages import PTCLMessage, BB84Message, SPDSMessage

LEADER_ROLE = 0
FOLLOW_ROLE = 1
IDLE_TIMEOUT = 60
BYTE_LEN = 8
ROUND_SIZE = 100
PCHSH = 0.8535533905932737
MAX_GOLAY_ERROR = 0.13043478260869565


class ProtocolException(Exception):
    pass


class QChatProtocol:
    def __init__(self, peer_info, connection, key_size, ctrl_msg_q, outbound_q, role, relay_info):
        """
        Initializes a protocol object that is used for executing quantum/classical exchange protocols
        :param peer_info:  Dictionary containing host, ip, port information
        :param connection: A QChatConnection object
        :param key_size:   The length of the key we wish to derive
        :param ctrl_msg_q: Queue containing inbound messages from our peer
        :param outbound_q: Queue containing outbound message to our peer
        :param role:       Either LEADER_ROLE or FOLLOW_ROLE for coordinating the protocol
        """
        self.logger = QChatLogger(__name__)

        # QChat connection interface
        self.connection = connection

        # The desired key size in bytes
        self.key_size = key_size

        # The inbound control message queue
        self.ctrl_msg_q = ctrl_msg_q

        # The outbound message queue
        self.outbound_q = outbound_q

        # Peer information for the communication in the protocol
        self.peer_info = peer_info

        # Qubit source relay information
        self.relay_info = relay_info

        # The role we are assuming for the protocol
        self.role = role

        # Perform perliminary steps of the protocol
        if role == LEADER_ROLE:
            self.device = LeadDevice(self.connection, self.relay_info)
            self._lead_protocol()
        elif role == FOLLOW_ROLE:
            self.device = FollowDevice(self.connection, self.relay_info)
            self._follow_protocol()

    def _lead_protocol(self):
        raise NotImplementedError

    def _follow_protocol(self):
        raise NotImplementedError

    def _wait_for_control_message(self, idle_timeout=IDLE_TIMEOUT, message_type=None):
        """
        Waits for a control message from our peer in blocking mode
        :param idle_timeout: The number of seconds to wait before aborting the protocol
        :param message_type: The type of control message we are expecting
        :return:             The message that we received
        """
        # Wait for a message
        wait_start = time.time()
        while not self.ctrl_msg_q:
            curr_time = time.time()

            if curr_time - wait_start > idle_timeout:
                raise ProtocolException("Timed out waiting for control message")

        # Grab the newest message
        message = self.ctrl_msg_q.pop(0)

        # Verify it is routed to the correct place
        if not isinstance(message, message_type):
            raise ProtocolException("Received incorrect control message")

        return message

    def _send_control_message(self, message_data, message_type):
        """
        Sends a control message to our peer
        :param message_data: The message data we want to send
        :param message_type: The type of message we want to send
        :return:
        """
        message = message_type(sender=self.connection.name, message_data=message_data)
        self.outbound_q.put((self.peer_info["user"], message))

    def exchange_messages(self, message_data, message_type):
        """
        Exchanges messages with our peer
        :param message_data: The message data we want to send
        :param message_type: The message type we are expecting/wanting to send
        :return:             The message we received from our peer
        """
        if self.role == LEADER_ROLE:
            self._send_control_message(message_data=message_data, message_type=message_type)
            return self._wait_for_control_message(message_type=message_type)
        else:
            m = self._wait_for_control_message(message_type=message_type)
            self._send_control_message(message_data=message_data, message_type=message_type)
            return m


class QChatKeyProtocol(QChatProtocol):
    def _lead_protocol(self):
        self._send_control_message(message_data={"name": self.name, "key_size": self.key_size},
                                   message_type=PTCLMessage)
        response = self._wait_for_control_message(message_type=self.message_type)
        if response.data["ACK"] != "ACK":
            raise ProtocolException("Failed to establish leader/role")

    def _follow_protocol(self):
        self._send_control_message(message_data={"ACK": "ACK"}, message_type=self.message_type)


class BB84_Purified(QChatKeyProtocol):
    """
    Implements the Purified BB84 protocol
    With a 16 byte key and noiseless channel we distribute a total of 1200 qubits between the participants
    """
    name = "BB84_PURIFIED"
    message_type = BB84Message
    def _receive_bb84_states(self):
        """
        Method is intended to receive the distributed qubits from the EPR pair.
        :return: A list of the measurement outcomes/basis used
        """
        # Lists for the measurement/basis information
        x = []
        theta = []

        # Distribute ROUND_SIZE qubits
        while len(x) < ROUND_SIZE:
            # Request our EPR source to distribute the pairs
            if self.role == LEADER_ROLE:
                self.device.requestEPR(self.peer_info["user"])

            # Receive our half of the EPR pair
            q = self.device.receiveEPR()

            # Randomly measure in Hadamard/Standard basis
            basisflip = random.randint(0, 1)
            if basisflip:
                q.H()

            # Store the measurement/basis information
            theta.append(basisflip)
            x.append(q.measure())

            # Let peer know we are ready for the next qubit
            r = self.exchange_messages(message_data={"ack": True}, message_type=BB84Message)
            if not r.data["ack"]:
                raise ProtocolException("Error distributing EPR states")

        return x, theta

    def _filter_theta(self, x, theta):
        """
        Used to filter our measurements that were done with differing basis between the two peers in the protocol
        :param x:       A list of the measurement outcomes
        :param theta:   A list of the basis used for producing the measurement outcomes
        :return:        The remaining measurement outcomes with matching basis with our peer
        """
        # Exchange basis information
        response = self.exchange_messages(message_data={"theta": theta}, message_type=BB84Message)
        theta_hat = response.data["theta"]

        x_remain = []
        for bit, basis, basis_hat in zip(x, theta, theta_hat):

            # Only retain measurements that were performed in the same basis
            if basis == basis_hat:
                x_remain.append(bit)

        return x_remain

    def _estimate_error_rate(self, x):
        """
        Estimates the error rate of the exchanged BB84 information
        :param x: The measurement outcomes obtained
        :param num_test_bits: The number of bits we should test
        :return: The error rate of the communicated information
        """
        test_bits = []
        test_indices = []

        # As leader we distribute the selected test indices
        if self.role == LEADER_ROLE:
            # Randomly choose a subset of indices to use for testing
            while len(test_indices) < ROUND_SIZE // 4 and len(x) > 0:
                # Choose a index we still have
                index = random.randint(0, len(x) - 1)

                # Store the test bit and index
                test_bits.append(x.pop(index))
                test_indices.append(index)

            # Send the information and wait for an acknowledgement
            r = self.exchange_messages(message_data={"test_indices": test_indices}, message_type=BB84Message)
            if not r.data["ack"]:
                raise ProtocolException("Error sending test indices")

        # As follower we receive the test indices
        elif self.role == FOLLOW_ROLE:
            # Receive the indices and respond with an acknowledgment
            m = self.exchange_messages(message_data={"ack": True}, message_type=BB84Message)
            test_indices = m.data["test_indices"]

            # Construct the test bit information on our end
            for index in test_indices:
                test_bits.append(x.pop(index))

        # Exchange test bits with our peer
        m = self.exchange_messages(message_data={"test_bits": test_bits}, message_type=BB84Message)
        target_test_bits = m.data["test_bits"]

        # Calculate the error rate of same basis bits
        num_error = 0
        for t1, t2 in zip(test_bits, target_test_bits):
            if t1 != t2:
                num_error += 1

        # Conclude the error estimation with our peer
        r = self.exchange_messages(message_data={"fin": True}, message_type=BB84Message)
        if not r.data["fin"]:
            raise ProtocolException("Error coordinating error estimation")

        return (num_error / len(test_bits))

    def _reconcile_information(self, x, ecc=ECC_Golay()):
        """
        Information Reconciliation based on linear codes
        :param x: Set of codewords
        :return: Bytestring of reconciled information
        """
        reconciled = []

        # Iterate through the codewords we have available
        for codeword in ecc.chunk(x):
            # Recycle any remaining codeword bits and the reconciled information
            if len(codeword) < ecc.codeword_length:
                return codeword, reconciled

            # As leader we send a syndrome string of the information we have
            if self.role == LEADER_ROLE:
                # Encode the codeword and send the information
                s = ecc.encode(codeword)
                m = self.exchange_messages(message_data={"s": s}, message_type=BB84Message)

                if not m.data["ack"]:
                    raise ProtocolException("Failed to reconcile secrets")

            # As follower we receive the error correcting codes and correct information on our end
            elif self.role == FOLLOW_ROLE:
                m = self.exchange_messages(message_data={"ack": True}, message_type=BB84Message)
                s = m.data["s"]

            # Store the reconciled information
            reconciled += ecc.decode(codeword, s)

        # Managed to have all valid length codewords, no remaining secret bits
        return [], reconciled

    def _amplify_privacy(self, X):
        """
        One-round privacy amplification sourced from https://eprint.iacr.org/2010/456.pdf
        :param X: A bytestring of the information we wish to distill
        :return: Privacy amplified byte from X
        """
        # As leader we select an Y to use as a seed for our extractor
        if self.role == LEADER_ROLE:
            # Select the seed
            Y = random.randint(0, 2 ** 8 - 1)

            # Calculate the extracted data and tag
            temp = (Y * X[0]).to_bytes(2, 'big')
            R = temp[0]
            T = temp[1] + X[1]

            # Send seed and tag to peer
            m = self.exchange_messages(message_data={"Y": Y, "T": T}, message_type=BB84Message)

            # If failure some information may not have been correctly reconciled
            if not m.data["ack"]:
                return b''

        # As follower we receive the seed and tag and verify the extracted data
        elif self.role == FOLLOW_ROLE:
            # Get seed/tag from peer
            m = self._wait_for_control_message(message_type=BB84Message)
            Y = m.data["Y"]
            T = m.data["T"]

            # Calculate the extracted information on our end
            temp = (Y * X[0]).to_bytes(2, 'big')

            # Verify the tag
            if T != X[1] + temp[1]:
                self._send_control_message(message_data={"ack": False}, message_type=BB84Message)
                return b''

            # Get extracted randomness if tag passes
            R = temp[0]
            self._send_control_message(message_data={"ack": True}, message_type=BB84Message)

        # Return extracted byte
        return R.to_bytes(1, 'big')

    def distill_tested_data(self):
        """
        A wrapper for distributing the BB84 states between the two users and tests the error rate
        of the measured data
        :return: A list of the shared secret bits
        """
        # Get measurement/basis data
        x, theta = self._receive_bb84_states()

        # Filter measurements we didn't match bases on
        x_remain = self._filter_theta(x=x, theta=theta)

        # Calculate the error rate of test information, remove the test data
        error_rate = self._estimate_error_rate(x_remain)

        # Abort the protocol if we have to high of an error rate to reconcile information with
        if error_rate >= MAX_GOLAY_ERROR:
            raise RuntimeError("Error rate of {}, aborting protocol".format(error_rate))

        # Return the secret data
        return x_remain

    def execute(self):
        """
        A wrapper for the entire key derivation protocol
        :return: Derived key of byte length key_size
        """
        key = b''
        secret_bits = []
        reconciled = []

        # Continue the protocol until we have a full key
        while len(key) < self.key_size:

            # Privacy amplification requires two bytes of reconciled data
            while len(reconciled) < 2*BYTE_LEN:

                # Golay Error Correction requires 23 bits of data per code word
                while len(secret_bits) < ECC_Golay.codeword_length:
                    secret_bits += self.distill_tested_data()
                    self.logger.debug("Secret bits: {}".format(secret_bits))

                # Reconcile codeword multiple of bits from the exchanged information
                secret_bits, reconciled_bits = self._reconcile_information(secret_bits)
                reconciled += reconciled_bits

            self.logger.debug("Reconciled: {}".format(reconciled))
            # Convert the reconciled data into bytes that can be passed to privacy amplifcation
            reconciled_bytes = int(''.join([str(i) for i in reconciled[:2*BYTE_LEN]]), 2).to_bytes(2, 'big')
            reconciled = reconciled[2*BYTE_LEN:]

            # Extract randomness from our reconciled information
            key += self._amplify_privacy(reconciled_bytes)
            self.logger.debug(key)

        self.logger.debug("Derived key {}".format(key))
        return key


class DIQKD(BB84_Purified):
    def _device_independent_distribute_bb84(self):
        x = []
        theta = [random.randint(0, 1) for _ in range(ROUND_SIZE)]
        device = LeadDevice(self.connection, self.relay_info)
        for b in theta:
            device.requestEPR(self.peer_info["user"])
            q = device.receiveEPR()
            x.append(device.measure(q, b))
            m = self.exchange_messages(message_data={"ack": True}, message_type=BB84Message)
            if not m.data["ack"]:
                raise ProtocolException("Error distributing DI states")

        return x, theta

    def _device_independent_receive_bb84(self):
        x = []
        theta = [random.randint(0, 2) for _ in range(ROUND_SIZE)]
        device = FollowDevice(self.connection, self.relay_info)
        for b in theta:
            q = device.receiveEPR()
            x.append(device.measure(q, b))
            m = self.exchange_messages(message_data={"ack": True}, message_type=BB84Message)
            if not m.data["ack"]:
                raise ProtocolException("Error receiving DI states")

        return x, theta

    def _device_independent_epr_test(self, x, theta):
        m = self.exchange_messages(message_data={"theta": theta}, message_type=BB84Message)
        theta_hat = m.data["theta"]
        if self.role == LEADER_ROLE:
            T = random.sample(range(len(x)), len(x) // 2)
            self._send_control_message(message_data={"T": T}, message_type=BB84Message)
            Tp = [j for j in T if theta_hat[j] in [0, 1]]
            Tpp = [j for j in T if theta[j] == 0 and theta_hat[j] == 2]
            R = [j for j in set(range(len(x))) - set(T) if theta[j] == 0 and theta_hat[j] == 2]

        elif self.role == FOLLOW_ROLE:
            m = self._wait_for_control_message(message_type=BB84Message)
            T = m.data["T"]
            Tp = [j for j in T if theta[j] in [0, 1]]
            Tpp = [j for j in T if theta_hat[j] == 0 and theta[j] == 2]
            R = [j for j in set(range(len(x))) - set(T) if theta_hat[j] == 0 and theta[j] == 2]

        x_T = [x[j] for j in T]
        m = self.exchange_messages(message_data={"x_T": x_T}, message_type=BB84Message)
        x_T_hat = m.data["x_T"]

        winning = [j for j, x1, x2 in zip(Tp, x_T, x_T_hat) if x1 ^ x2 == theta[j] & theta_hat[j]]
        p_win = len(winning) / len(Tp)
        matching = [j for j, x1, x2 in zip(Tpp, x_T, x_T_hat) if x1 == x2]
        p_match = len(matching) / len(Tpp)

        e = 0.1
        if p_win < PCHSH - e or p_match < 1 - e:
            self.logger.debug(x_T)
            self.logger.debug(x_T_hat)
            self.logger.debug("CHSH Winners: {} out of {}".format(len(winning), Tp))
            self.logger.debug("Matching: {} out of {}".format(len(matching), Tpp))
            raise ProtocolException("Failed to pass CHSH test: p_win: {} p_match: {}".format(p_win, p_match))

        x_remain = [x[r] for r in R]
        return x_remain

    def distill_device_independent_data(self):
        if self.role == LEADER_ROLE:
            x, theta = self._device_independent_distribute_bb84()
        elif self.role == FOLLOW_ROLE:
            x, theta = self._device_independent_receive_bb84()

        x_remain = self._device_independent_epr_test(x, theta)

        return x_remain


class QChatMessageProtocol(QChatProtocol):
    def _lead_protocol(self):
        self._send_control_message(message_data={"name": self.name}, message_type=PTCLMessage)
        response = self._wait_for_control_message(message_type=SPDSMessage)
        if response.data["ACK"] != "ACK":
            raise ProtocolException("Failed to establish leader/role")

    def _follow_protocol(self):
        self._send_control_message(message_data={"ACK": "ACK"}, message_type=self.message_type)


class SuperDenseCoding(QChatMessageProtocol):
    """
    Implements sending SuperDense Coded data
    """
    name = "SUPERDENSE"
    message_type = SPDSMessage
    def send_message(self, message):
        user = self.peer_info["user"]
        for b in message:
            for p in range(4):
                b2 = (b >> 2*p) & 1
                b1 = (b >> (2*p) + 1) & 1

                q = self.connection.cqc.createEPR(user)
                m = self.exchange_messages(message_data={"ack":True}, message_type=SPDSMessage)
                if not m.data["ack"]:
                    raise ProtocolException("Failed to send {}'s qubit".format(user))
                if b2:
                    q.X()
                if b1:
                    q.Z()
                self.connection.cqc.sendQubit(q, user)
                m = self.exchange_messages(message_data={"ack": True}, message_type=SPDSMessage)
                if not m.data["ack"]:
                    raise ProtocolException("Failed to send EPR to {}".format(user))
                m = self._wait_for_control_message(message_type=SPDSMessage)
                if not m.data["ack"]:
                    raise ProtocolException("Failed to send EPR to {}".format(user))

        self.exchange_messages(message_data={"fin": True}, message_type=SPDSMessage)

    def receive_message(self):
        user = self.peer_info["user"]
        message = b''
        while True:
            m = self.exchange_messages(message_data={"ack": True}, message_type=SPDSMessage)
            if m.data.get("fin"):
                return message
            elif not m.data["ack"]:
                raise ProtocolException("Error receiving qubit")
            b = 0
            for p in range(4):
                q = self.connection.cqc.recvEPR()
                m = self.exchange_messages(message_data={"ack": True}, message_type=SPDSMessage)
                if not m.data["ack"]:
                    raise ProtocolException("Failed to send {}'s qubit".format(user))
                q2 = self.connection.cqc.recvQubit()
                q.cnot(q2)
                q2.H()
                b |= (q.measure() << 2*p)
                b |= (q2.measure() << (2*p + 1))
                self._send_control_message(message_data={"ack": True}, message_type=SPDSMessage)
            message += b.to_bytes(1, 'big')



class ProtocolFactory:
    def __init__(self):
        self.protocol_mapping = {
            BB84_Purified.name: BB84_Purified,
            SuperDenseCoding.name: SuperDenseCoding
        }

    def createProtocol(self, name):
        return self.protocol_mapping.get(name)