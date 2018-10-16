import threading
from collections import defaultdict
from QChat.log import QChatLogger


class DBException(Exception):
    pass


class UserDB:
    def __init__(self):
        """
        Initializes a user database for holding QChat contact information
        """
        self.lock = threading.Lock()
        self.logger = QChatLogger(__name__)
        self.db = defaultdict(dict)

    def _get_user(self, user):
        return self.db.get(user)

    def hasUser(self, user):
        return self._get_user(user) is not None

    def getPublicKey(self, user):
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        return info.get('pub')

    def getMessageKey(self, user):
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        return info.get('message_key')

    def getConnectionInfo(self, user):
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        return info.get('connection')

    def deleteUserInfo(self, user, fields):
        self.logger.debug("Deleting user {} info {}".format(user, fields))
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        for field in fields:
            info.pop(field)

    def deleteUser(self, user):
        self.logger.debug("Deleting user {}".format(user))
        self.db.pop(user)

    def changeUserInfo(self, user, **kwargs):
        self.logger.debug("Changing user {} with data {}".format(user, kwargs))
        if self.hasUser(user):
            self.db[user].update(kwargs)

    def addUser(self, user, **kwargs):
        self.logger.debug("Adding user {} with data {}".format(user, kwargs))
        self.db[user].update(kwargs)

    def getPublicUserInfo(self, user):
        if user == "*":
            public_info = []
            for user in self.db:
                info = {
                    "connection": self.getConnectionInfo(user),
                    "pub": self.getPublicKey(user)
                }

                info["pub"] = info["pub"].decode("ISO-8859-1")
                info["user"] = user

                public_info.append(info)

            public_info = {"user": "*", "info": public_info}

        else:
            public_info = {
                "connection": self.getConnectionInfo(user),
                "pub": self.getPublicKey(user)
            }

            public_info["pub"] = public_info["pub"].decode("ISO-8859-1")
            public_info["user"] = user

        return public_info