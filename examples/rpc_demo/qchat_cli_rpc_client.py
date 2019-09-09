# pylint: disable=missing-docstring
import argparse
import logging
import sys
from qchat.rpc import QChatCLIRPCClient

"""
Sample RPC client that runs a dialog box between two users
"""


def main():
    """
    Runs the RPCClient using the provided information
    :return:
    """
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
