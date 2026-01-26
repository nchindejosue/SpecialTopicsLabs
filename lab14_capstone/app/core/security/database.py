import sqlite3
import os
import bcrypt

class SecurityDB:
    def __init__(self, db_path="app_security.db"):
        self.db_path = db_path
        self.init_db()
        # Seed admin account if not exists
        if not self.user_exists("admin"):
            self.create_account("admin", "admin123", "admin")

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    password_hash BLOB,
                    role TEXT DEFAULT 'developer'
                )
            """)
            conn.commit()

    def user_exists(self, username):
        with sqlite3.connect(self.db_path) as conn:
            return conn.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone() is not None

    def create_account(self, username, password, role='developer'):
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                             (username, hashed, role))
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate(self, username, password):
        with sqlite3.connect(self.db_path) as conn:
            user = conn.execute("SELECT password_hash, role FROM users WHERE username=?", (username,)).fetchone()
            if user and bcrypt.checkpw(password.encode('utf-8'), user[0]):
                return True, user[1]
        return False, None
