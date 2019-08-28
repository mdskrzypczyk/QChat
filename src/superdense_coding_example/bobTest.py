import time
from QChat.client import QChatClient

# Sleep for 4 seconds
time.sleep(4)

# Set up Bob and spin
client = QChatClient("Bob")
while True:
    messages = client.getMessageHistory()
    if messages:
        print("Got messages!: {}".format(messages))
        break
    time.sleep(10)
