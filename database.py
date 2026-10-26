import sqlite3
from config import DATABASE_PATH

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
        self.init_database()

    def init_database(self):
        """Inicializa o banco de dados e cria a tabela se não existir"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id)
            )
        ''')

        conn.commit()
        conn.close()

    def add_user(self, user_id, username=None, first_name=None, last_name=None):
        """Adiciona um usuário ao banco de dados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))

            conn.commit()
            return True
        except Exception as e:
            print(f"Erro ao adicionar usuário: {e}")
            return False
        finally:
            conn.close()

    def get_user(self, user_id):
        """Busca um usuário pelo ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = cursor.fetchone()

        conn.close()
        return user

    def get_all_users(self):
        """Retorna todos os usuários cadastrados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM users ORDER BY timestamp DESC')
        users = cursor.fetchall()

        conn.close()
        return users

    def get_user_count(self):
        """Retorna o número total de usuários cadastrados"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]

        conn.close()
        return count
