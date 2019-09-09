import time
from qchat.client import QChatClient
from qchat.server import QChatServer
from cqc.pythonLib import CQCConnection

def main():
    # Create Simulaqron connections for each component
    with CQCConnection(name="Alice") as cqc_alice, CQCConnection(name="Bob") as cqc_bob, \
            CQCConnection(name="Eve") as cqc_eve:

        # Start up root server
        root = QChatServer(name="Eve", cqc_connection=cqc_eve)
        time.sleep(2)

        # Start up users
        alice_client = QChatClient(name="Alice", cqc_connection=cqc_alice)
        bob_client = QChatClient(name="Bob", cqc_connection=cqc_bob)
        time.sleep(2)

        # Send a superdense coded message
        alice_client.sendSuperDenseMessage("Bob", "Hello!")

        while True:
            messages = bob_client.getMessageHistory()
            if messages:
                print("Got messages!: {}".format(messages))
                break
            time.sleep(1)

        bob_client.sendSuperDenseMessage("Alice", "Hello to you too!")

        while True:
            messages = alice_client.getMessageHistory()
            if messages:
                print("Got messages!: {}".format(messages))
                break
            time.sleep(1)


if __name__ == "__main__":
    main()
