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
    """
    An RPC Server that connects to a QChatServer
    """

    clients = {}

    def __init__(self, user, host, port, client):
        """
        Initializes the RPC server
        :param user: str
            The name of the QChatServer
        :param host: str
            The host to receive RPC commands at
        :param port: int
            The port to receive RPC commands at
        :param client: `~qchat.client.QChatClient`
            The QChatClient to interact with
        """
        self.user = user
        self.host = host
        self.port = port
        self.clients[user] = client
        self._ensure_client_for(user)
        self.logger = QChatLogger("QChatClientRPCServer-{}".format(user))
        self.logger.debug("Starting server for {} at {}:{}".format(user, host, port))

    def send_message(self, user, destination, message):
        """
        Listens for a send message RPC call and forwards the command to the underlying QChatClient
        :param user: str
            The name of the client to use
        :param destination: str
            The name of the peer to send the message to
        :param message: str
            The plaintext message to send
        :return: bool
            Whether message was sent or not
        """
        self._ensure_client_for(user)
        try:
            self.clients[user].sendQChatMessage(destination, message)
            return True

        except Exception:
            return False

    def get_messages(self, user):
        """
        RPC call for retrieving messages from the client
        :param user: str
            The client to retrieve messages for
        :return: dict
            A dictionary of message lists keyed by the sender
        """
        self._ensure_client_for(user)
        messages = {}
        self.logger.info("Fetching messages from {}".format(user))
        try:
            messages = dict(self.clients[user].getMessageHistory())
            if messages:
                self.logger.info("Received messages {} for user {}".format(messages, user))

        except Exception:
            self.logger.exception("Failed getting messages from {}".format(user))

        return messages

    def _ensure_client_for(self, user):
        """
        Checks that the specified user has a client that is running, if not sets one up
        :param user:
        :return:
        """
        if user not in self.clients:
            self.clients[user] = QChatClient(user)
            # wait for registration
            time.sleep(2)


class QChatCLIRPCClient:
    """
    Simple RPC client that sends messages to an RPCServer
    """
    def __init__(self, user, destination, server_url):
        """
        Initializes the RPC client
        :param user: str
            The user we wish to send a message as
        :param destination: str
            The peer we wish to send a message to
        :param server_url: str
            The RPCServer url to connect to, eg. http://127.0.0.1:6666
        """
        self.client = xmlrpc.client.ServerProxy(server_url)
        self.user = user
        self.destination = destination
        self._running = False
        self._message_reader = threading.Thread(target=self._read_messages)
        self.lock = threading.Lock()
        self.logger = QChatLogger("QChatCLIRPCClient-{}".format(user))

    def start(self):
        """
        Starts the RPC client and sends messages based on user input
        :return: None
        """
        print("Hello, this is {}".format(self.user))
        self._running = True
        self._message_reader.start()

        while self._running:
            input_text = input("\n[ {} ]: ".format(self.user))
            the_message = "{} @ {}".format(input_text, time.time())
            with self.lock:
                self.client.send_message(self.user, self.destination, the_message)

    def stop(self):
        """
        Stops the RPC Client
        :return: None
        """
        self.logger.info("Stopping the CLI RPC Client")
        self._running = False
        self._message_reader.join()

    def _read_messages(self):
        """
        Polls the RPCServer for messages that belong to the user running the RPC client
        :return: None
        """
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
