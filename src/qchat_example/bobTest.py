import time
from QChat.client import QChatClient

# Sleep for 4 seconds
time.sleep(2)

# Set up the server
c = QChatClient("Bob")

# Spin to keep the server alive
while True:
    messages = c.getMessageHistory("Bob")
    if messages:
        print("Got messages!: {}".format(messages))
        break
    time.sleep(10)

c.sendQChatMessage("Alice", "Hello to you!")

while True:
    time.sleep(10)