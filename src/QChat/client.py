from QChat.server import QChatServer


class QChatClient:
    def logOut(self):
        self.server.close()

    def logIn(self, user):
        self.server = QChatServer(user)

    def getContacts(self, verbose=False):
        return self.server.get_contact_info(verbose)

    def sendMessage(self, user: str, message_data: str):
        return self.server.send_qchat_message(user, message_data)

    def getMailboxInfo(self):
        return self.server.get_mailbox_info()

    def getMessages(self, user, count):
        return self.server.get_messages(user, count)

    def sendQubit(self, user, qubit_info):
        return self.server.send_qubit_message(user, qubit_info)

    def shareEPR(self, user):
        return self.server.create_shared_epr(user)

    def updatePublicKey(self):
        return self.server.update_public_key()
