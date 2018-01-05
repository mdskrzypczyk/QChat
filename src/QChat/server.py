from db import UserDB
from Cipher.PublicKey import RSA, DSA


class QChatServer:
    def __init__(self):
        self.connection = QChatConnection()
        self.userDB = UserDB()

    def hasUser(self, user):
        return self.userDB.hasUser(user)

    def addUser(self, user):
        self.userDB.addUser(user)

    def registerUser(self, user, password):
        if self.hasUser(user):

        else:
            self.user

    def getUserInfo(self):
        pass

    def pushMessages(self):
        pass

    def getMessages(self):
        pass

    def verifyUser(self):
        pass
