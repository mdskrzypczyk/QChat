import pytest
import json
from qchat.messages import MalformedMessage, Message, RGSTMessage, AUTHMessage, QCHTMessage, MessageFactory


class TestMessage:
    @classmethod
    def setup_class(cls):
        cls.test_sender = "Alice"
        cls.test_data = "TEST"
        cls.test_message_data = {
            "user": cls.test_sender,
            "data": cls.test_data
        }

    def test_Message(self):
        test_message = Message(self.test_sender, self.test_message_data)
        assert test_message.header == Message.header
        assert test_message.sender == self.test_sender
        assert test_message.data == self.test_message_data
        assert test_message.encode_message() == bytes("MSSG" + "\x00"*11 + self.test_sender +
                                                      "\x00\x00\x00!" + json.dumps(self.test_message_data), 'utf-8')

        test_message = Message(self.test_sender, json.dumps(self.test_message_data))
        assert test_message.header == Message.header
        assert test_message.sender == self.test_sender
        assert test_message.data == self.test_message_data
        assert test_message.encode_message() == bytes("MSSG" + "\x00"*11 + self.test_sender +
                                                      "\x00\x00\x00!" + json.dumps(self.test_message_data), 'utf-8')

        with pytest.raises(MalformedMessage):
            Message("a"*17, self.test_message_data)

        bad_data = b"Not JSON Serializable"
        with pytest.raises(MalformedMessage):
            test_message.unpack_message_data(bad_data)

        test_message.data = bad_data
        with pytest.raises(MalformedMessage):
            test_message.encode_message()

    def test_RGSTMessage(self):
        test_rgst_message = RGSTMessage(self.test_sender, self.test_message_data)
        assert test_rgst_message.header == RGSTMessage.header

    def test_AUTHMessage(self):
        test_rgst_message = AUTHMessage(self.test_sender, self.test_message_data)
        assert test_rgst_message.header == AUTHMessage.header

    def test_QCHTMessage(self):
        test_rgst_message = QCHTMessage(self.test_sender, self.test_message_data)
        assert test_rgst_message.header == QCHTMessage.header


class TestMessageFactory:
    @classmethod
    def setup_class(cls):
        cls.message_data = {"user": "Alice"}
        cls.sender = "Alice"

    def test_factory(self):
        message_mapping = MessageFactory().message_mapping
        for header, cls in message_mapping.items():
            message = MessageFactory().create_message(header, self.sender, self.message_data)
            assert type(message) == cls
            assert message.sender == self.sender
            assert message.header == header
            assert message.data == self.message_data
