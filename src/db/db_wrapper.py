import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

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

    def close(self):
        try:
            if self.conn and self.conn.is_connected():
                self.conn.close()
                self.conn = None
        except Exception as e:
            print("Error closing connection:", e)
