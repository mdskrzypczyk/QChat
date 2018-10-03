import time
from QChat.server import QChatServer

# Sleep for 10 seconds to allow Bob to spin up
time.sleep(10)

# Set up the server
s = QChatServer("Alice")
time.sleep(2)

# Send a superdense coded message
s.sendSuperDenseMessage("Bob", "Hello!")
