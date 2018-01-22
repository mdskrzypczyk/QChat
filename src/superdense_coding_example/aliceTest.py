import time
from QChat.server import QChatServer


time.sleep(10)
s = QChatServer("Alice")
time.sleep(2)
s.sendSuperDenseMessage("Bob", "Hello!")
