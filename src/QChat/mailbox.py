import threading
from collections import defaultdict
from QChat.log import QChatLogger


class QChatMailbox:
    """
    Implements a thread safe message storing mailbox
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.messages = defaultdict(list)
        self.logger = QChatLogger(__name__)

    def storeMessage(self, message):
        self.logger.info("New message in mailbox from {}".format(message.sender))
        with self.lock:
            self.messages[message.sender].append(message)

    def getMessages(self, user):
        self.logger.info("Retrieving messages for {}".format(user))
        with self.lock:
            return list(self.messages[user])