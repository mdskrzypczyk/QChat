from QChat.server import QChatServer
import time
time.sleep(10)
s = QChatServer("Alice")
time.sleep(2)
s.sendQChatMessage("Bob", "Hello!")
