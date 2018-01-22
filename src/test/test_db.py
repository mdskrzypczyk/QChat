from QChat.db import UserDB


class TestUserDB:
    @classmethod
    def setup_class(cls):
        cls.test_db = UserDB()
        cls.test_user = "test"
        cls.test_entry = {"connection": {"host": "localhost", "port": 1337}, "pub": "Test Pub"}

    def test_get_user(self):
        assert self.test_db._get_user(self.test_user) == {}
        assert self.test_db.hasUser(self.test_user) == False
        self.test_db.addUser(self.test_user, **self.test_entry)
        assert self.test_db._get_user(self.test_user) == self.test_entry
        assert self.test_db.hasUser(self.test_user) == True

    def test_get_info(self):
        self.test_db.addUser(self.test_user, **self.test_entry)
        assert self.test_db.getPublicKey(self.test_user) == self.test_entry["pub"]
        assert self.test_db.getConnectionInfo(self.test_user) == self.test_entry["connection"]
        assert self.test_db.getPublicInfo(self.test_user) == self.test_entry
        assert self.test_db.getMessageKey(self.test_user) == None
        self.test_db.changeUserInfo(self.test_user, message_key=b'test')
        assert self.test_db.getMessageKey(self.test_user) == b'test'

    def test_change_info(self):
        self.test_db.addUser(self.test_user, **self.test_entry)
        self.test_db.changeUserInfo(self.test_user, pub="New Pub")
        assert self.test_db.getPublicKey(self.test_user) == "New Pub"

    def test_delete(self):
        self.test_db.addUser(self.test_user, **self.test_entry)
        self.test_db.deleteUserInfo(self.test_user, ["connection"])
        assert self.test_db.getConnectionInfo(self.test_user) == None
        assert self.test_db.hasUser(self.test_user) == True
        self.test_db.deleteUser(self.test_user)
        assert self.test_db.hasUser(self.test_user) == False
