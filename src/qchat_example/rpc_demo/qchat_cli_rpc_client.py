# pylint: disable=missing-docstring
import argparse
import logging
import sys
import time

import xmlrpc.client

from threading import Thread

logger = logging.getLogger("QChatCLIRPCCline")
logger.setLevel(logging.DEBUG)


class QChatCLIRPCClient:
    def __init__(self, user, destination, server_url):
        self.client = xmlrpc.client.ServerProxy(server_url)
        self.user = user
        self.destination = destination
        self._running = False
        self._message_reader = Thread(target=self._read_messages)

    def start(self):
        self._running = True
        self._message_reader.start()

        while self._running:
            input_text = input("[ {} ]: ".format(self.user))
            the_message = "%s @ %f" % (input_text, time.time())
            self.client.send_message(self.user, self.destination, the_message)

    def stop(self):
        logger.info("Stopping the CLI RPC Client")
        self._running = False
        self._message_reader.join()

    def _read_messages(self):
        while self._running:
            try:
                user_messages = self.client.get_messages(self.user)
                for sender, messages in user_messages.items():
                    for message in messages:
                        print("[ {} ]: {}\n".format(sender, message))
            except:
                logger.exception("Failed getting messages for %s", self.user)
                time.sleep(2)
            time.sleep(1)


def main():
    logging.basicConfig()
    args = _parse_args()
    qchat_client = QChatCLIRPCClient(args.user, args.destination, args.server_url)
    try:
        qchat_client.start()
    except KeyboardInterrupt:
        qchat_client.stop()
        sys.exit(0)


def _parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--user",
                        help="The user for which to start the client",
                        choices=["Bob", "Alice"],
                        required=True)
    parser.add_argument("--destination",
                        help="The user to which to send messages",
                        choices=["Bob", "Alice"],
                        required=True)
    parser.add_argument("--server-url",
                        help="Host of the RPC server. eg: http://127.0.0.1:33333",
                        required=True)
    parsed_args = parser.parse_args(args)
    if parsed_args.user == parsed_args.destination:
        parser.error("User and destination can't be the same")
    return parsed_args

if __name__ == "__main__":
    main()
