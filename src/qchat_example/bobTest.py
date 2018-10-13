import time
from QChat.client import QChatClient

# Sleep for 4 seconds
time.sleep(4)

# Set up the server
s = QChatClient("Bob")

# Spin to keep the server alive
while True:
    pass
