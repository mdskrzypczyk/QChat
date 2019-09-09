import threading
from qchat.log import QChatLogger


class QChatMailbox:
    """
    Implements a thread safe message storing mailbox
    """
    def __init__(self):
        self.lock = threading.Lock()
        self.messages = []
        self.logger = QChatLogger(__name__)

    def storeMessage(self, message):
        """
        Stores a message into the mailbox
        :param message: obj
            The message to store
        :return: None
        """
        self.logger.debug("New message in mailbox from {}".format(message.sender))
        with self.lock:
            self.messages.append(message)

    def getMessages(self):
        """
        Returns a list of the messages that are currently stored in the mailbox
        :return: list
            A list of the messages that are currently stored
        """
        self.logger.debug("Retrieving messages")
        with self.lock:
            return list(self.messages)

    def popMessages(self):
        """
        Pops all messages that are stored and returns them
        :return: list
            List of the stored messages that were removed
        """
        self.logger.debug("Popping messages")
        with self.lock:
            messages = list(self.messages)
            self.messages = []
            return messages
