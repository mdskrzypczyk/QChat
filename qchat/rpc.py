import time
import threading
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCRequestHandler
from qchat.client import QChatClient
from qchat.log import QChatLogger


# Restrict to a particular path.
class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ('/RPC2',)


class QChatRPCServer:

    clients = {}

    def __init__(self, user, host, port, client):
        self.user = user
        self.host = host
        self.port = port
        self.clients[user] = client
        self._ensure_client_for(user)
        self.logger = QChatLogger("QChatClientRPCServer-{}".format(user))
        self.logger.debug("Starting server for {} at {}:{}".format(user, host, port))

    def send_message(self, user, destination, message):
        self._ensure_client_for(user)
        try:
            self.clients[user].sendQChatMessage(destination, message)
            return True

        except Exception:
            return False

    def get_messages(self, user):
        self._ensure_client_for(user)
        messages = {}
        self.logger.info("Fetching messages from {}".format(user))
        try:
            messages = dict(self.clients[user].getMessageHistory())
            if messages:
                self.logger.info("Received messages {} from user {}".format(messages, user))

        except Exception:
            self.logger.exception("Failed getting messages from {}".format(user))

        return messages

    def _ensure_client_for(self, user):
        if user not in self.clients:
            self.clients[user] = QChatClient(user)
            # wait for registration
            time.sleep(2)


class QChatCLIRPCClient:
    def __init__(self, user, destination, server_url):
        self.client = xmlrpc.client.ServerProxy(server_url)
        self.user = user
        self.destination = destination
        self._running = False
        self._message_reader = threading.Thread(target=self._read_messages)
        self.lock = threading.Lock()
        self.logger = QChatLogger("QChatCLIRPCClient-{}".format(user))

    def start(self):
        print("Hello, this is {}".format(self.user))
        self._running = True
        self._message_reader.start()

        while self._running:
            input_text = input("\n[ {} ]: ".format(self.user))
            the_message = "{} @ {}".format(input_text, time.time())
            with self.lock:
                self.client.send_message(self.user, self.destination, the_message)

    def stop(self):
        self.logger.info("Stopping the CLI RPC Client")
        self._running = False
        self._message_reader.join()

    def _read_messages(self):
        while self._running:
            try:
                with self.lock:
                    user_messages = self.client.get_messages(self.user)
                if user_messages:
                    print("\n")
                    for sender, messages in user_messages.items():
                        for message in messages:
                            print("[ {} ]: {}\n".format(sender, message))
                    print("[ {} ]: ".format(self.user), end="")

            except Exception:
                self.logger.exception("Failed getting messages for {}".format(self.user))
                time.sleep(2)
            time.sleep(1)
