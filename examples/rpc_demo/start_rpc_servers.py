import time
import sys
from qchat.client import QChatClient
from qchat.server import QChatServer
from cqc.pythonLib import CQCConnection
from qchat.rpc import QChatRPCServer, RequestHandler
from threading import Thread
from xmlrpc.server import SimpleXMLRPCServer

CLIENTS = {
    "Alice": 33333,
    "Bob": 33334
}

SERVER_THREADS = {}


class RPCServerThread(Thread):
    def __init__(self, server, target):
        super(RPCServerThread, self).__init__()
        self.running = True
        self.server = server

    def run(self):
        self.server.serve_forever()

    def stop(self):
        self.server.shutdown()
        self.server.server_close()


def start_rpc_server(user, host, port, client):
    if user not in SERVER_THREADS.keys():
        # Create server
        server = SimpleXMLRPCServer((host, port), requestHandler=RequestHandler)
        server.register_instance(QChatRPCServer(user, host, port, client))
        server_thread = RPCServerThread(server=server, target=server.serve_forever)
        SERVER_THREADS[user] = server_thread
        server_thread.start()


def main():
    with CQCConnection(name="Alice") as cqc_alice, CQCConnection(name="Bob") as cqc_bob, \
            CQCConnection(name="Eve") as cqc_eve:
        # Start up root server
        root = QChatServer(name="Eve", cqc_connection=cqc_eve)
        time.sleep(2)

        # Start up users
        alice_client = QChatClient(name="Alice", cqc_connection=cqc_alice)
        bob_client = QChatClient(name="Bob", cqc_connection=cqc_bob)

        start_rpc_server(user="Alice", host="127.0.0.1", port=CLIENTS["Alice"], client=alice_client)
        start_rpc_server(user="Bob", host="127.0.0.1", port=CLIENTS["Bob"], client=bob_client)

        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
            for user, server_thread in SERVER_THREADS.items():
                print("Closing RPC server for {}".format(user))
                server_thread.stop()
            sys.exit(0)


if __name__ == "__main__":
    main()
