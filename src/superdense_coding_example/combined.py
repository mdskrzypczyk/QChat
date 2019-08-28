import time
from QChat.client import QChatClient
from QChat.server import QChatServer

# Set up the root server and spin
root = QChatServer("Eve")

# Set up the server
time.sleep(2)
alice_client = QChatClient("Alice")

# Sleep for 4 seconds
time.sleep(2)

# Set up the server
bob_client = QChatClient("Bob")
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
