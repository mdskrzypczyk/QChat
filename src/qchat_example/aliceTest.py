from QChat.client import QChatClient
import time

# Sleep for 10 seconds to allow Bob to spin up first
time.sleep(4)

# Instantiate the server and sleep for 2 seconds to allow initialization
c = QChatClient("Alice")
time.sleep(2)

# Send a message to Bob
c.sendQChatMessage("Bob", "Hello!")

while True:
    pass
