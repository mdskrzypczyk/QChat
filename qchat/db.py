import threading
from collections import defaultdict
from qchat.log import QChatLogger


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
        """
        Retrieves a user's data in the database
        :param user: str
            Name of the user
        :return: dict
            Stored data
        """
        return self.db.get(user)

    def hasUser(self, user):
        """
        Checks if the database has the specified user
        :param user: str
            The name of the user
        :return: bool
            Whether user exists in database or not
        """
        return self._get_user(user) is not None

    def getPublicKey(self, user):
        """
        Returns the stored public key of the specified user
        :param user: str
            The name of the user
        :return: bytes
            The public key data
        """
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        return info.get('pub')

    def getMessageKey(self, user):
        """
        Retrieves the key used for encrypting/decrypting messages
        :param user: str
            The name of the user
        :return: bytes
            The key associated with the specified user
        """
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        return info.get('message_key')

    def getConnectionInfo(self, user):
        """
        Retrieves connection information for the specified user
        :param user: str
            The name of the user
        :return: dict
            Contains connection details of the user
        """
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        return info.get('connection')

    def deleteUserInfo(self, user, fields):
        """
        Deletes all specified fields of data for the user
        :param user: str
            Name of the user
        :param fields: list
            List of strings of the names of the fields to delete
        :return: None
        """
        self.logger.debug("Deleting user {} info {}".format(user, fields))
        info = self._get_user(user)
        if not info:
            raise DBException("User {} does not exist in the database!")
        for field in fields:
            info.pop(field)

    def deleteUser(self, user):
        """
        Deletes a user from the database
        :param user: str
            The name of the user
        :return: None
        """
        self.logger.debug("Deleting user {}".format(user))
        self.db.pop(user)

    def changeUserInfo(self, user, **kwargs):
        """
        Updates a user entry in the database
        :param user: str
            The name of the user
        :param kwargs: dict
            A dictionary of updates to merge for the user
        :return: None
        """
        self.logger.debug("Changing user {} with data {}".format(user, kwargs))
        if self.hasUser(user):
            self.db[user].update(kwargs)

    def addUser(self, user, **kwargs):
        """
        Adds a user into the database along with any initial data
        :param user: str
            The name of the user
        :param kwargs: dict
            The initial data to store for the user
        :return: None
        """
        self.logger.debug("Adding user {} with data {}".format(user, kwargs))
        self.db[user].update(kwargs)

    def getPublicUserInfo(self, user):
        """
        Returns the public information of a user including the connection details and public key
        :param user: str
            The name of the user
        :return: dict
            Contains public information of the user
        """
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
