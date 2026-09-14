import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
if os.path.exists(env_path):
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

class DBWrapper:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port,
                use_pure=True
            )
        except Exception as e:
            print("Connection error:", e)
            self.conn = None
        return self.conn

    def get_connection(self):
        try:
            if self.conn is None or not self.conn.is_connected():
                self.connect()
        except Exception:
            self.connect()
        return self.conn

    def execute_query(self, query, params=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print("Error executing query:", e)
            if self.conn:
                self.conn.rollback()
            return False

    def fetch_all(self, query, params=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            print("Error fetching all:", e)
            return []

    def fetch_one(self, query, params=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor(dictionary=True, buffered=True)
            cursor.execute(query, params or ())
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            print("Error fetching one:", e)
            return None

    def execute_many(self, query, data):
        try:
            conn = self.get_connection()
            cursor = conn.cursor(buffered=True)
            cursor.executemany(query, data)
            conn.commit()
            cursor.close()
            return True
        except Exception as e:
            print("Error executing many:", e)
            if self.conn:
                self.conn.rollback()
            return False

    def query_df(self, sql, params=None):
        import pandas as pd
        try:
            conn = self.get_connection()
            return pd.read_sql(sql, conn, params=params)
        except Exception as e:
            print("Error fetching dataframe:", e)
            return pd.DataFrame()

    def close(self):
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                self.conn = None
        except Exception as e:
            print("Error closing connection:", e)
