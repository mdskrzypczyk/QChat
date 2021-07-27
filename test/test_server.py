import os

from qchat.server import QChatServer


class mock_qubit:
    pass


class mock_cqc:
    qubits = {}

    def __init__(self, user):
        self.user = user
        self.qubits[self.user] = {'epr': [], 'qubits': []}

    def createEPR(self, user):
        our_qubit, their_qubit = mock_qubit(), mock_qubit()
        self.qubits[user]['epr'].append(their_qubit)
        return our_qubit

    def recvEPR(self):
        has_epr = self.qubits[self.user]['epr'] != []
        epr = self.qubits[self.user]['epr'].pop(0) if has_epr else None
        return epr

    def sendQubit(self, q, user):
        self.qubits[user]['qubits'].append(q)

    def recvQubit(self):
        has_qubit = self.qubits[self.user]['qubits'] != []
        qubit = self.qubits[self.user]['qubits'].pop(0) if has_qubit else None
        return qubit


class TestQChatServerUnit:
    def setup_class(cls):
        cls.test_user = "User"
        cls.test_config = {"host": "localhost", "port": 8000}
        cls.test_config_path = os.path.join(os.path.dirname(__file__), 'resources', 'test_server_config.json')

    def teardown_class(cls):
        pass

    def test_object(self):
        server = QChatServer(name=self.test_user, configFile=self.test_config_path,
                             cqc_connection=mock_cqc(self.test_user))
        assert server.name == self.test_user

    def test_process_message(self):
        pass


class TestQChatServerIntegration:
    def setup_class(cls):
        cls.test_user = "User"
        cls.test_config = {"host": "localhost", "port": 8000}
        cls.test_config_path = os.path.join(os.path.dirname(__file__), 'resources', 'test_config.json')
        cls.server = QChatServer(name=cls.test_user, cqc_connection=mock_cqc(cls.test_user))
