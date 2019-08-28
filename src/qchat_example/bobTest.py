import time
from QChat.client import QChatClient

# Sleep for 4 seconds
time.sleep(2)

# Set up the server
client = QChatClient("Bob")

# Spin to keep the server alive
while True:
    messages = client.getMessageHistory()
    if messages:
        print("Got messages!: {}".format(messages))
        break
    time.sleep(10)

client.sendQChatMessage("Alice", "Hello to you!")