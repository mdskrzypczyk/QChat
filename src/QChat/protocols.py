from QChat.messages import BB84Message


class ProtocolException(Exception):
    pass


class QChatKeyProtocol:
    def __init__(self, connection, n):
        self.cqc = connection.cqc
        self.n = n


class BB84(QChatProtocol):
    def _distribute_bb84_states(self, user, eavesdropper="Eve"):
        x = []
        theta = []
        while len(x) < n:
            q = self.cqc.createEPR(eavesdropper)
            bitflip = random.randint(0, 1)
            if bitflip:
                q.X()
            basisflip = random.randint(0, 1)
            if basisflip:
                q.H()

            x.append(q.measure())
            theta.append(basisflip)

        return x, theta

    def _filter_theta(self, user, x, theta):
        x_remain = []
        bb84_data = {"data": theta}
        bb84_message = BB84Message(self.connection.name, message_data=bb84_data)
        self.connection.send_message()
        sendClassicalAssured(cqc, target, theta)
        theta_hat = recvClassicalAssured(cqc, target)
        for bit, basis, basis_hat in zip(x, theta, theta_hat):
            if basis == basis_hat:
                x_remain.append(bit)

        return x_remain

    def execute(self, user):
        x, theta = self._distribute_bb84_states(user=user)
        m = self.connection.wait_for_control_response(header=BB84Message.header, user=user)
        if m.data.get("message") != "States received":
            raise ProtocolException("Failed to transmit BB84 states")

        x_remain = self._filter_theta(user=user, x=x, theta=theta)
