import threading
from collections import defaultdict


class QChatMailbox:
    def __init__(self):
        self.lock = threading.Lock()
        self.messages = defaultdict(list)

    def storeMessage(self, message):
        with self.lock:
            self.messages[message.sender].append(message)

    def getMessage(self, user):
        with self.lock:
            return self.messages[user].pop(0) if self.messages.get(user) else None