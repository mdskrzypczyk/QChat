import logging
import time

from xmlrpc.server import SimpleXMLRPCRequestHandler

from QChat.client import QChatClient


logger = logging.getLogger("QChatClientRPCServer")
logger.setLevel(logging.DEBUG)


class QChatRPCServer():

    clients = {}

    def __init__(self, user):
        self.user = user
        self._ensure_client_for(user)

    def send_message(self, user, destination, message):
        self._ensure_client_for(user)
        try:
            self.clients[user].sendQChatMessage(destination, message)
            return True
        except:
            return False

    def get_messages(self, user):
        self._ensure_client_for(user)
        messages = {}
        logger.info("Trying to get user messages for %s", user)
        try:
            messages = dict(self.clients[user].getMessageHistory())
            logger.info("Hurra got message %s for user %s", messages, user)
        except:
            logger.exception("Failed getting messages for user %s", user)
        return messages

    def _ensure_client_for(self, user):
        if user not in self.clients:
            self.clients[user] = QChatClient(user, allow_invalid_signatures=True)
            # wait for registration
            time.sleep(2)


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)
