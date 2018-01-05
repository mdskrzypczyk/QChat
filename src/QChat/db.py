import sqlite3
from sqlite3 import Error
from log import QChatLogger


def DBException(Exception):
    pass


def TableFormat:
    def __init__(self, column_tuple):
        self.info = column_tuple

    def __str__(self):
        info_str = "({})".format(" ".join(["{} {} {}".format(v_name, v_type, v_opts) in self.info]))
        return info_str

def EntryInfo:
    def __init__(self, **kwargs):
        self.info = kwargs

    def __str__(self):
        keys, values = [], []
        for k, v in self.info:
            keys.append(k)
            values.append(v)
        return " ".join(keys), " ".join(values)


def EquivalenceInfo(EntryInfo):
    def __str__(self):
        " ".join(["{} = {}".format(k, v) for k, v in self.info.items()])


def DB(self):
    def __init__(self, name, config):
        self.conn = None
        self.name = name
        self.logger = QChatLogger()
        self.db_file = config['db_file']

    def __del__(self):
        self._disconnect_from_db()

    def _connect_to_db():
        if not self.conn:
            try:
                self.loger.debug("Connecting to database at {}".format(self.db_file))
                self.conn = sqlite3.connect(self.db_file)
                self.logger.debug("Successfully connected to database at {}".format(self.db_file))
            except Error as e:
                self.logger.error("Failed to connect to database at {} with error:\n{}".format(e))
                raise DBException("Error connecting to database")
        else:
            self.logger.error("Attempted to double create database at {}".format(self.db_file))

    def _disconnect_from_db():
        if self.conn:
            try:
                self.logger.debug("Disconnecting from database at {}, saving".format(self.db_file))
                self.conn.close()
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
            self.logger.error("Failed to add entry to table with error:\n{}".format(e))
        return None

    def _create_table(self, name, table_info):
        return self._db_operation("CREATE TABLE IF NOT EXISTS {} ({});".format(name, table_info))

    def _has_table(self, name):
        return self._db_operation("SELECT name FROM sqlite_master WHERE type='table' AND name={};".format(name))

    def _add_entry(self, table_name, entry_info):
        return self._db_operation("INSERT INTO {} ({}) VALUES ({});".format(table_name, entry_info))

    def _get_entry(self, table_name, search_criteria):
        return self._db_operation("SELECT entry FROM {} WHERE {}".format(table_name, search_criteria))

    def _delete_entry(self, table_name, search_criteria):
        return self._db_operation("DELETE FROM {} WHERE {}".format(table_name, search_criteria))

    def _delete_all_entries(self, table_name):
        return self._db_operation("DELETE FROM {}".format(table_name))

    def _edit_entry(self, table_name, edit_info, search_criteria):
        return self._db_operation("UPDATE {} SET {} WHERE {}".format(table_name, edit_info, search_criteria))

def UserDB(DB):
    def __init__(self):

    def addUser(self):
        pass

    def deleteUser(self):
        pass

    def editUser(self):
        pass

    def getUser(self):
        pass


def MessageDB(DB):
    pass