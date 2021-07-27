from qchat.mailbox import QChatMailbox
from qchat.messages import Message


class TestMailbox:
    @classmethod
    def setup_class(cls):
        cls.test_user = "User"
        cls.message_data = {"data": "test_data"}
        cls.test_message = Message(sender=cls.test_user, message_data=cls.message_data)

    def test_storeMessage(self):
        m = QChatMailbox()
        m.storeMessage(self.test_message)
        [stored] = m.messages
        assert stored.sender == self.test_message.sender
        assert stored.header == self.test_message.header
        assert stored.data == self.test_message.data

    def test_getMessage(self):
        m = QChatMailbox()
        assert m.getMessages() == []
        m.messages = [self.test_message]
        assert m.getMessages() == [self.test_message]

    def test_store_get(self):
        m = QChatMailbox()
        m.storeMessage(self.test_message)
        stored = m.getMessages()[0]
        assert stored.sender == self.test_message.sender
        assert stored.header == self.test_message.header
        assert stored.data == self.test_message.data
