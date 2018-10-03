import time
from QChat.server import QChatServer

# Sleep for 4 seconds
time.sleep(4)

# Set up the server
s = QChatServer("Bob")

# Spin to keep the server alive
while True:
    pass