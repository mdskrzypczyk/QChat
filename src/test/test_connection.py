import threading
import pytest
from QChat.connection import QChatConnection, ConnectionError
from QChat.messages import Message


class mock_connection:
    def __init__(self, buffer):
        self.buffer = buffer

    def recv(self, count):
        if self.buffer:
            data = self.buffer[:count]
            self.buffer = self.buffer[count:]
            return data
        else:
            return None

    def close(self):
        pass


class TestQChatConnection:
    @classmethod
    def setup_class(cls):
        cls.test_name = "Alice"
        cls.test_sender = "Bob"
        cls.test_message = 'abcd'
        cls.test_message_data = {"user": cls.test_sender}
        cls.test_addr = 'localhost'
        cls.test_config1 = {"host": "localhost", "port": 8000}
        cls.test_config2 = {"host": "localhost", "port": 8001}

    def test_QChatConnection(self):
        connection = QChatConnection(name=self.test_name, config=self.test_config1)
        assert connection.name == self.test_name
        assert connection.host == self.test_config1['host']
        assert connection.port == self.test_config1['port']
        assert type(connection.lock) == type(threading.Lock())
        assert connection.message_queue == []

    def test_get_message(self):
        connection = QChatConnection(name=self.test_name, config=self.test_config1)
        connection.message_queue.append(self.test_message)
        assert connection.get_message() == self.test_message
        assert connection.message_queue == []

    def test_insert_message_into_queue(self):
        connection = QChatConnection(name=self.test_name, config=self.test_config1)
        connection._insert_message_into_queue(self.test_message)
        assert connection.message_queue[0] == self.test_message

    def test_listen_for_connection(self):
        connection = QChatConnection(name=self.test_name, config=self.test_config1)

    def test_handle_connection(self):
        connection = QChatConnection(name=self.test_name, config=self.test_config1)
        # Invalid header
        mc = mock_connection("abcd")
        with pytest.raises(ConnectionError) as ce:
            connection._handle_connection(mc, self.test_addr)
            assert str(ce) == "Incorrect message header"

        # Invalid sender length
        mc = mock_connection("MSSGtestsender1234567")
        with pytest.raises(ConnectionError) as ce:
            connection._handle_connection(mc, self.test_addr)
            assert str(ce) == "Incorrect sender length"

        # Invalid sender
        mc = mock_connection("MSSG" + "\x00"*16)
        with pytest.raises(ConnectionError) as ce:
            connection._handle_connection(mc, self.test_addr)
            assert str(ce) == "Invalid sender"

        # Invalid payload byte size
        mc = mock_connection("MSSG" + "\x00"*11 + "Alice" + "abc")
        with pytest.raises(ConnectionError) as ce:
            connection._handle_connection(mc, self.test_addr)
            assert str(ce) == "Incorrect payload size"

        # Invalid payload
        payload = "testing"
        str_size = "\x00\x00\x00\x08"
        mc = mock_connection("MSSG" + "\x00"*11 + "Alice" + str_size + payload)
        with pytest.raises(ConnectionError) as ce:
            connection._handle_connection(mc, self.test_addr)
            assert str(ce) == "Message data too short"

        payload = "testingtesting"
        mc = mock_connection("MSSG" + "\x00" * 11 + "Alice" + str_size + payload)
        with pytest.raises(ConnectionError) as ce:
            connection._handle_connection(mc, self.test_addr)
            assert str(ce) == "Message data too long"

        # Valid message
        message = Message(self.test_sender, self.test_message_data)
        mc = mock_connection(message.encode_message())
        connection._handle_connection(mc, self.test_addr)
        assert connection.message_queue[0] is not None

    def test_send_message(self):
        pass
