import time
from QChat.client import QChatClient

# Sleep for 10 seconds to allow Bob to spin up
time.sleep(10)

# Set up the server
client = QChatClient("Alice")
time.sleep(2)

# Send a superdense coded message
client.sendSuperDenseMessage("Bob", "Hello!")
