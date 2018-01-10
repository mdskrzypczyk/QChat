import threading
from collections import defaultdict


class QChatMailbox:
    def __init__(self):
        self.lock = theading.Lock()
        self.messages = defaultdict(list)

    def storeMessage(self, message):
        self.messages[message.sender].append(message)

