import sqlite3
import hashlib
from datetime import datetime

def init_db():
    conn = sqlite3.connect('fake_news_detector.db')
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create analysis history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS analysis_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            content TEXT NOT NULL,
            result TEXT NOT NULL,
            trust_score INTEGER,
            fake_probability INTEGER,
            analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, password, email):
    conn = sqlite3.connect('fake_news_detector.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                 (username, hash_password(password), email))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('fake_news_detector.db')
    c = conn.cursor()
    c.execute('SELECT id, username FROM users WHERE username = ? AND password = ?',
             (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def save_analysis(user_id, content, result, trust_score, fake_probability):
    conn = sqlite3.connect('fake_news_detector.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO analysis_history 
        (user_id, content, result, trust_score, fake_probability)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, content, result, trust_score, fake_probability))
    conn.commit()
    conn.close()

def get_user_history(user_id):
    conn = sqlite3.connect('fake_news_detector.db')
    c = conn.cursor()
    c.execute('''
        SELECT content, result, trust_score, fake_probability, analysis_date
        FROM analysis_history
        WHERE user_id = ?
        ORDER BY analysis_date DESC
    ''', (user_id,))
    history = c.fetchall()
    conn.close()
    return history

def delete_analysis(user_id, date):
    try:
        conn = sqlite3.connect('fake_news_detector.db')
        c = conn.cursor()
        c.execute('DELETE FROM analysis_history WHERE user_id = ? AND analysis_date = ?', 
                 (user_id, date))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting analysis: {e}")
        return False 