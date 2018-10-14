import time
from QChat.client import QChatClient

# Sleep for 4 seconds
time.sleep(2)

# Set up the server
s = QChatClient("Bob")

# Spin to keep the server alive
while True:
    print(s.mailbox.messages)
    try:
        print("Got messages!: {}".format(s.getMessageHistory("Alice")))
    except:
        pass
    time.sleep(10)
