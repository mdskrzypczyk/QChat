from qchat.server import QChatServer


class TestQChatServerUnit:
    def setup_class(cls):
        cls.test_user = "User"
        cls.test_config = {"host": "localhost", "port": 8000}

    def teardown_class(cls):
        pass

    def test_object(self):
        server = QChatServer(name=self.test_user, config=self.test_config)
        assert server.name == self.test_user

    def test_process_message(self):
        pass


class TestQChatServerIntegration:
    def setup_class(cls):
        cls.test_user = "User"
        cls.test_config = {"host": "localhost", "port": 8000}
        cls.server = QChatServer(name=cls.test_user, test_config=cls.test_config)
