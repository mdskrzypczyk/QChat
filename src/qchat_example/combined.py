import time
from QChat.client import QChatClient
from QChat.server import QChatServer

# Set up the root server and spin
root = QChatServer("Eve")
time.sleep(2)

alice_client = QChatClient("Alice")
time.sleep(2)

bob_client = QChatClient("Bob")
time.sleep(2)

# Send a message to Bob
alice_client.sendQChatMessage("Bob", "Hello!")

# Spin to keep the server alive
while True:
    messages = bob_client.getMessageHistory()
    if messages:
        print("Got messages!: {}".format(messages))
        break
    time.sleep(10)

bob_client.sendQChatMessage("Alice", "Hello to you!")

# Spin to keep the server alive
while True:
    messages = alice_client.getMessageHistory()
    if messages:
        print("Got messages!: {}".format(messages))
        break
    time.sleep(10)
