import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name='bot_database.db'):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """Инициализация базы данных и создание таблицы messages"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            response TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def save_message(self, user_id: int, username: str, message: str, response: str):
        """Сохранение сообщения и ответа в базу данных"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO messages (user_id, username, message, response)
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, message, response))
        
        conn.commit()
        conn.close()

    def get_recent_messages(self, user_id: int, limit: int = 20):
        """Получение последних сообщений пользователя"""
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT message, response, timestamp
        FROM messages
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (user_id, limit))
        
        messages = cursor.fetchall()
        conn.close()
        
        return messages
