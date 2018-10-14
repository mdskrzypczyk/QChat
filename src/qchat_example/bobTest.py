import time
from QChat.client import QChatClient

# Sleep for 4 seconds
time.sleep(2)

# Set up the server
s = QChatClient("Bob")

# Spin to keep the server alive
while True:
    messages = s.getMessageHistory("Bob")
    if messages:
        print("Got messages!: {}".format(messages))
        break
    time.sleep(10)

s.requestUserInfo('*')
time.sleep(5)