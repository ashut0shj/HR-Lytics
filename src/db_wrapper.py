import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


class DBWrapper:
    """
    Thin wrapper around a mysql-connector connection.

    Handles reconnection automatically, so callers don't need to think
    about whether the connection is still alive after an idle period.
    """

    def __init__(self, database=None):
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.port = int(os.getenv("DB_PORT", 3306))
        if database is not None:
            self.database = database
        else:
            self.database = os.getenv("DB_NAME", "")
        self.conn = None
        self.connect()

    def connect(self):
        try:
            kwargs = {
                "host": self.host,
                "user": self.user,
                "password": self.password,
                "port": self.port,
                "use_pure": True,
                "autocommit": True,
            }
            if self.database:
                kwargs["database"] = self.database
            self.conn = mysql.connector.connect(**kwargs)
        except Exception as e:
            print(f"DB connection error: {e}")
            self.conn = None
        return self.conn

    def get_connection(self):
        """Return an active connection, reconnecting if necessary."""
        try:
            if self.conn is None or not self.conn.is_connected():
                self.connect()
        except Exception:
            self.connect()
        return self.conn

    def is_healthy(self) -> bool:
        """Check if database connection is alive and working."""
        try:
            conn = self.get_connection()
            return conn is not None and conn.is_connected()
        except Exception:
            return False

    def execute_query(self, query, params=None):
        """Run a single DML statement (INSERT / UPDATE / DELETE). Returns True on success."""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"execute_query error: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def call_procedure(self, proc_call: str) -> bool:
        """Execute a `CALL proc(...)` statement, draining any result sets it leaves behind."""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            cursor = conn.cursor()
            cursor.execute(f"CALL {proc_call}")
            while cursor.nextset():
                pass
            cursor.close()
            return True
        except Exception as e:
            print(f"call_procedure error: {e}")
            return False

    def execute_many(self, query, data):
        """Batch-insert using executemany. Returns True on success."""
        try:
            conn = self.get_connection()
            if not conn:
                return False
            cursor = conn.cursor(buffered=True)
            cursor.executemany(query, data)
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print(f"execute_many error: {e}")
            if self.conn:
                self.conn.rollback()
            return False

    def fetch_all(self, query, params=None):
        """Return a list of dicts for a SELECT query. Empty list on error."""
        try:
            conn = self.get_connection()
            if not conn:
                return []
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"fetch_all error: {e}")
            return []

    def fetch_one(self, query, params=None):
        try:
            conn = self.get_connection()
            if not conn:
                return None
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f"fetch_one error: {e}")
            return None

    def query_df(self, sql, params=None):
        import pandas as pd
        try:
            conn = self.get_connection()
            if not conn:
                return pd.DataFrame()
            return pd.read_sql(sql, conn, params=params)
        except Exception as e:
            print(f"query_df error: {e}")
            return pd.DataFrame()

    def close(self):
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                self.conn = None
        except Exception as e:
            print(f"close error: {e}")

