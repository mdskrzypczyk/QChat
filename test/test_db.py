from QChat.db import DB
from os.path import exists, unlink


class TestDB:
    def setUp(cls):
        cls.test_config =  {"db_file": "testDB.sqlite3"}
        cls.test_table_info = [("v1", "integar","PRIMARY KEY"),
                               ("v2", "text", "NOT NULL")]
        cls.test_database = DB(name="testDB")
        cls.test_entry_1 = {"v1": "1", "v2": "test1"}
        cls.test_entry_2 = {"v1": "2", "v2": "test2"}

    def tearDown(cls):
        cls.test_database._disconnect_from_db()
        if exists(cls.test_config['db_file']):
            unlink(cls.test_config['db_file'])

    def testObject(self):
        assert self.test_database.name == "TestDB"
        assert self.test_database.conn == None
        assert self.test_database.logger
        assert self.test_database.db_file == self.test_config['db_file']

    def testConnections(self):
        self.test_database._connect_to_db()
        assert exists(self.test_config['db_file'])
        assert self.test_database.conn

        self.test_database._disconnect_from_db()
        assert exists(self.test_config['db_file'])
        assert self.test_database.conn == None

    def testTable(self):
        self.test_database._connect_to_db()
        self.test_database._create_table("TestTable", self.test_table_info)
        assert self.test_database._has_table("TestTable")
        assert self.test_database._has_table("TestTable2") == False

        self.test_database._add_entry("TestTable", self.test_entry_1)
        assert self.test_database._get_entry("TestTable", self.test_entry_1) == self.test_entry_1
        assert self.test_database._get_entry("TestTable", self.test_entry_2) == None

        self.test_database._edit_entry("TestTable", self.test_entry_2, self.test_entry_1)
        assert self.test_database._get_entry("TestTable") == self.test_entry_2

        self.test_database._delete_entry("TestTable", self.test_entry_1)
        assert self.test_database._has_entry(self.test_entry_1) == False

        self.test_database._add_entry("TestTable", self.test_entry_1)
        self.test_database._add_entry("TestTable", self.test_entry_2)
        self.test_database._delete_all_entries("TestTable")
        assert self.test_database._get_entry("TestTable", self.test_entry_1) == None
        assert self.test_database._get_entry("TestTable", self.test_entry_2) == None


class TestUserDB:
    pass

class TestMessageDB:
    pass
