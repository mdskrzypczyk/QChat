import threading
from collections import defaultdict
from QChat.log import QChatLogger


class QChatMailbox:
    """
    Implements a thread safe message storing mailbox
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.messages = []
        self.logger = QChatLogger(__name__)

    def storeMessage(self, message):
        self.logger.info("New message in mailbox from {}".format(message.sender))
        with self.lock:
            self.messages.append(message)

    def getMessages(self):
        self.logger.info("Retrieving messages")
        with self.lock:
            return list(self.messages)

    def popMessages(self):
        self.logger.info("Popping messages")
        with self.lock:
            messages = list(self.messages)
            self.messages = []
            return messages