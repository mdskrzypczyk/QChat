import os
import json
from QChat.server import QChatServer
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256


def load_config(user):
    path = os.path.abspath(__file__)
    config_path = os.path.dirname(path) + "/config.json"
    with open(config_path) as f:
        config = jsonload(f)
    return config[user] if config.get(user) else None


class QChatClient:
    def __init__(self, user: str):
        self.server_config = load_config(user)
        self.server = QChatServer(user, self.server_config)

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
