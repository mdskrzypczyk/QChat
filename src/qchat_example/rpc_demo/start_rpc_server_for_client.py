import argparse
import logging
import sys

from xmlrpc.server import SimpleXMLRPCServer

from QChat.client_rpc_server import QChatRPCServer, RequestHandler

CLIENTS = {
    "Bob": 33333,
    "Alice": 33334,
}

logger = logging.getLogger("QChatClientRPCServer")
logger.setLevel(logging.DEBUG)


def main():
    logging.basicConfig()
    args = _parse_args()

    # Create server
    server = SimpleXMLRPCServer((args.host, CLIENTS[args.user]),
                                requestHandler=RequestHandler)
    server.register_instance(QChatRPCServer(args.user))
    # Run the server's main loop
    logger.info("starting server for %s on port %s host %s",
                args.user, CLIENTS[args.user], args.host)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        sys.exit(0)


def _parse_args(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--user",
                        help="The User for which to start the client",
                        choices=CLIENTS.keys(),
                        required=True)
    parser.add_argument("--host",
                        help="Host of the RPC server.",
                        default="0.0.0.0")
    return parser.parse_args()


if __name__ == "__main__":
    main()
