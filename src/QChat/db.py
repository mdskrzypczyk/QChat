import sqlite3
import threading
from sqlite3 import Error
from collections import defaultdict
from QChat.log import QChatLogger


class DBException(Exception):
    pass


class TableFormat:
    def __init__(self, column_tuple):
        self.info = column_tuple

    def __str__(self):
        info_str = "({})".format(", ".join(["{} {} {}".format(v_name, v_type, v_opts) for v_name, v_type, v_opts,
                                           in self.info]))
        return info_str

class EntryInfo:
    def __init__(self, **kwargs):
        self.info = kwargs

    def kvtup(self):
        keys, values = [], []
        for k, v in self.info.items():
            keys.append(str(k))
            if type(v) == str:
                values.append("'{}'".format(v))
            else:
                values.append(str(v))
        return ", ".join(keys), ", ".join(values)


class EquivalenceInfo(EntryInfo):
    def __str__(self):
        " ".join(["{} = {}".format(k, v) for k, v in self.info.items()])


class DB:
    def __init__(self, name, config):
        self.conn = None
        self.name = name
        self.logger = QChatLogger(name)
        self.db_file = config['db_file']

    def __del__(self):
        self._disconnect_from_db()

    def _connect_to_db(self):
        if not self.conn:
            try:
                self.logger.debug("Connecting to database at {}".format(self.db_file))
                self.conn = sqlite3.connect(self.db_file)
                self.logger.debug("Successfully connected to database at {}".format(self.db_file))
            except Error as e:
                self.logger.error("Failed to connect to database at {} with error:\n{}".format(e))
                raise DBException("Error connecting to database")
        else:
            self.logger.error("Attempted to double create database at {}".format(self.db_file))

    def _disconnect_from_db(self):
        if self.conn:
            try:
                self.logger.debug("Disconnecting from database at {}, saving".format(self.db_file))
                self.conn.close()
                self.conn = None
                self.logger.debug("Successfully closed connection to database at {}".format(self.db_file))
            except Error as e:
                self.logger.error("Failed to close connection to database at {} with error:\n{}".format(self.db_file, e))
                raise DBException("Error disconnecting from database")
        else:
            self.logger.error("Attempted to double disconnect from database at {}".format(self.db_file))

    def _db_operation(self, sql):
        try:
            c = self.conn.cursor()
            return c.execute(sql)
        except Error as e:
            self.logger.error("Failed perform operation {} with error:\n{}".format(sql, e))
        return None

    def _create_table(self, name, table_info):
        return self._db_operation("CREATE TABLE IF NOT EXISTS {} {};".format(name, table_info))

    def _has_table(self, name):
        res = self._db_operation("SELECT name FROM sqlite_master WHERE type='table' AND name='{}';".format(name))
        return res.fetchone() != None

    def _add_entry(self, table_name, entry_info):
        kvtup = entry_info.kvtup()
        return self._db_operation("INSERT INTO {} ({}) VALUES ({});".format(table_name, kvtup[0], kvtup[1]))

    def _get_entry(self, table_name, search_criteria):
        return self._db_operation("SELECT entry FROM {} WHERE {}".format(table_name, search_criteria)).fetchone()

    def _delete_entry(self, table_name, search_criteria):
        return self._db_operation("DELETE FROM {} WHERE {}".format(table_name, search_criteria))

    def _delete_all_entries(self, table_name):
        return self._db_operation("DELETE FROM {}".format(table_name))

    def _edit_entry(self, table_name, edit_info, search_criteria):
        return self._db_operation("UPDATE {} SET {} WHERE {}".format(table_name, edit_info, search_criteria))


class UserDB:
    def __init__(self):
        self.lock = threading.Lock()
        self.db = defaultdict(dict)

    def _get_user(self, user):
        return self.db.get(user)

    def hasUser(self, user):
        return self._get_user(user) is not None

    def getPublicKey(self, user):
        return self._get_user(user).get('pub')

    def getMessageKey(self, user):
        return self._get_user(user).get('message_key')

    def getConnectionInfo(self, user):
        return self._get_user(user).get('connection')

    def deleteUserInfo(self, user, fields):
        user_info = self.db._get_user(user)
        for field in fields:
            user_info.pop(field)

    def deleteUser(self, user):
        self.db.pop(user)

    def changeUserInfo(self, user, **kwargs):
        self.db[user].update(kwargs)

    def addUser(self, user, **kwargs):
        self.db[user].update(kwargs)

    def getPublicUserInfo(self, user):
        public_info = {
            "connection": self.getConnectionInfo(user),
            "pub": self.getPublicKey(user)
        }
        return public_info


class MessageDB(DB):
    pass