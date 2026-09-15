import os
import mysql.connector
from dotenv import load_dotenv

# Load .env from the project root. python-dotenv handles the path resolution
# and will silently do nothing if the file doesn't exist.
load_dotenv()

class DBWrapper:
    """
    Thin wrapper around a mysql-connector connection.

    Handles reconnection automatically, so callers don't need to think
    about whether the connection is still alive after an idle period.
    """

    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.conn = None
        self.connect()

    # ------------------------------------------------------------------
    # Connection management
    # ------------------------------------------------------------------

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                use_pure=True,
            )
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

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def execute_query(self, query, params=None):
        """Run a single DML statement (INSERT / UPDATE / DELETE). Returns True on success."""
        try:
            conn = self.get_connection()
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

    def execute_many(self, query, data):
        """Batch-insert using executemany. Returns True on success."""
        try:
            conn = self.get_connection()
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

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def fetch_all(self, query, params=None):
        """Return a list of dicts for a SELECT query. Empty list on error."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print(f"fetch_all error: {e}")
            return []

    def fetch_one(self, query, params=None):
        """Return the first row as a dict, or None on error / no results."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print(f"fetch_one error: {e}")
            return None

    def query_df(self, sql, params=None):
        """Run a SELECT and return the results as a pandas DataFrame."""
        import pandas as pd
        try:
            conn = self.get_connection()
            return pd.read_sql(sql, conn, params=params)
        except Exception as e:
            print(f"query_df error: {e}")
            return pd.DataFrame()

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def close(self):
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                self.conn = None
        except Exception as e:
            print(f"close error: {e}")
