"""
User database management for Smart Kitchen application
"""
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
import secrets
import string

class UserDatabase:
    def __init__(self, db_path="users.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL,
                    email TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    remember_token TEXT
                )
            ''')
            
            # Create password_reset_tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    token TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    used BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            ''')
            
            conn.commit()
    
    def _hash_password(self, password):
        """Hash password using SHA-256 with salt"""
        salt = secrets.token_hex(16)
        return hashlib.sha256((password + salt).encode()).hexdigest() + ':' + salt
    
    def _verify_password(self, password, stored_hash):
        """Verify password against stored hash"""
        stored_hash, salt = stored_hash.split(':')
        return stored_hash == hashlib.sha256((password + salt).encode()).hexdigest()
    
    def create_user(self, username, password, role="user", email=None):
        """Create a new user"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                password_hash = self._hash_password(password)
                cursor.execute('''
                    INSERT INTO users (username, password_hash, role, email)
                    VALUES (?, ?, ?, ?)
                ''', (username, password_hash, role, email))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate_user(self, username, password, remember=False):
        """Authenticate user and return user info if successful"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, password_hash, role, remember_token
                FROM users WHERE username = ?
            ''', (username,))
            user = cursor.fetchone()
            
            if user and self._verify_password(password, user[2]):
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (user[0],))
                
                # Generate remember token if requested
                if remember:
                    token = secrets.token_hex(32)
                    cursor.execute('''
                        UPDATE users SET remember_token = ?
                        WHERE id = ?
                    ''', (token, user[0]))
                    conn.commit()
                    return {
                        'id': user[0],
                        'username': user[1],
                        'role': user[3],
                        'remember_token': token
                    }
                
                conn.commit()
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[3]
                }
            return None
    
    def verify_remember_token(self, username, token):
        """Verify remember token for automatic login"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, username, role
                FROM users WHERE username = ? AND remember_token = ?
            ''', (username, token))
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'role': user[2]
                }
            return None
    
    def request_password_reset(self, email):
        """Generate and store password reset token"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            
            if user:
                token = secrets.token_hex(32)
                expires_at = datetime.now() + timedelta(hours=24)
                cursor.execute('''
                    INSERT INTO password_reset_tokens (user_id, token, expires_at)
                    VALUES (?, ?, ?)
                ''', (user[0], token, expires_at))
                conn.commit()
                return token
            return None
    
    def reset_password(self, token, new_password):
        """Reset password using token"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_id, expires_at, used
                FROM password_reset_tokens
                WHERE token = ?
            ''', (token,))
            reset_token = cursor.fetchone()
            
            if reset_token and not reset_token[2] and datetime.now() < datetime.fromisoformat(reset_token[1]):
                password_hash = self._hash_password(new_password)
                cursor.execute('''
                    UPDATE users SET password_hash = ?
                    WHERE id = ?
                ''', (password_hash, reset_token[0]))
                cursor.execute('''
                    UPDATE password_reset_tokens SET used = TRUE
                    WHERE token = ?
                ''', (token,))
                conn.commit()
                return True
            return False
    
    def change_password(self, user_id, current_password, new_password):
        """Change password for authenticated user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
            stored_hash = cursor.fetchone()[0]
            
            if self._verify_password(current_password, stored_hash):
                new_hash = self._hash_password(new_password)
                cursor.execute('''
                    UPDATE users SET password_hash = ?
                    WHERE id = ?
                ''', (new_hash, user_id))
                conn.commit()
                return True
            return False 