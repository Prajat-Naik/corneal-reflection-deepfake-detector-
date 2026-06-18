import os
import sqlite3
from werkzeug.security import generate_password_hash

# Connection Parameters
MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
MYSQL_USER = os.environ.get('MYSQL_USER', '')  # Leave blank by default to auto-fallback to SQLite
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
MYSQL_DB = os.environ.get('MYSQL_DB', 'forensics_db')

class DatabaseManager:
    def __init__(self):
        self.engine = 'sqlite'
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'forensics.db')
        self.mysql_config = {
            'host': MYSQL_HOST,
            'user': MYSQL_USER,
            'password': MYSQL_PASSWORD,
            'database': MYSQL_DB
        }
        self.initialize_engine()

    def initialize_engine(self):
        """Attempts to connect to MySQL; falls back to local SQLite on any exception/if unconfigured."""
        if not self.mysql_config['user']:
            print("[Database Manager] No MySQL credentials. Using local SQLite.")
            self.engine = 'sqlite'
            self.init_sqlite_db()
            return

        try:
            import mysql.connector
            # Create DB if it doesn't exist
            conn = mysql.connector.connect(
                host=self.mysql_config['host'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password']
            )
            cursor = conn.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.mysql_config['database']}")
            conn.close()

            self.engine = 'mysql'
            print(f"[Database Manager] Connected to MySQL database '{MYSQL_DB}' at {MYSQL_HOST}.")
            self.init_mysql_db()
        except Exception as e:
            print(f"[Database Manager] WARNING: MySQL Connection Failed: {e}. Falling back to SQLite.")
            self.engine = 'sqlite'
            self.init_sqlite_db()

    def get_connection(self):
        """Returns connection and cursor object for active engine."""
        if self.engine == 'mysql':
            import mysql.connector
            conn = mysql.connector.connect(
                host=self.mysql_config['host'],
                user=self.mysql_config['user'],
                password=self.mysql_config['password'],
                database=self.mysql_config['database']
            )
            return conn, conn.cursor(dictionary=True)
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn, conn.cursor()

    def execute_query(self, query, params=None):
        """Executes query mapping placeholders dynamically ('?' for SQLite vs '%s' for MySQL)."""
        if params is None:
            params = ()

        if self.engine == 'sqlite':
            query = query.replace('%s', '?')
        else:
            query = query.replace('?', '%s')

        conn, cursor = self.get_connection()
        try:
            cursor.execute(query, params)
            if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP')):
                conn.commit()
                last_id = cursor.lastrowid
                return last_id
            else:
                return cursor.fetchall()
        except Exception as e:
            print(f"[Database Manager] SQL Error: {e}")
            raise e
        finally:
            cursor.close()
            conn.close()

    def execute_query_one(self, query, params=None):
        results = self.execute_query(query, params)
        return results[0] if results else None

    def init_sqlite_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable foreign keys
        cursor.execute("PRAGMA foreign_keys = ON")

        # 1. users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                status TEXT CHECK(status IN ('ACTIVE', 'INACTIVE')) NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 2. admins
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 3. Analysis_History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Analysis_History (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                media_name TEXT NOT NULL,
                result TEXT CHECK(result IN ('REAL', 'DEEPFAKE')) NOT NULL,
                confidence REAL NOT NULL,
                trust_score INTEGER NOT NULL,
                rsi REAL NOT NULL,
                crcs REAL NOT NULL,
                ssim REAL NOT NULL,
                explanation TEXT NOT NULL,
                face_confidence REAL NOT NULL,
                face_coords TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        # 4. reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                analysis_id INTEGER,
                report_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES Analysis_History(id) ON DELETE CASCADE
            )
        ''')

        # 5. activity_logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 6. Email_Notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Email_Notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                analysis_id INTEGER,
                email TEXT NOT NULL,
                delivery_status TEXT CHECK(delivery_status IN ('SENT', 'FAILED')) NOT NULL,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (analysis_id) REFERENCES Analysis_History(id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        self._seed_default_users(cursor, conn)
        conn.close()

    def init_mysql_db(self):
        import mysql.connector
        conn = mysql.connector.connect(
            host=self.mysql_config['host'],
            user=self.mysql_config['user'],
            password=self.mysql_config['password'],
            database=self.mysql_config['database']
        )
        cursor = conn.cursor()

        # 1. users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                status ENUM('ACTIVE', 'INACTIVE') NOT NULL DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')

        # 2. admins
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')

        # 3. Analysis_History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Analysis_History (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                media_name VARCHAR(255) NOT NULL,
                result ENUM('REAL', 'DEEPFAKE') NOT NULL,
                confidence FLOAT NOT NULL,
                trust_score INT NOT NULL,
                rsi FLOAT NOT NULL,
                crcs FLOAT NOT NULL,
                ssim FLOAT NOT NULL,
                explanation TEXT NOT NULL,
                face_confidence FLOAT NOT NULL,
                face_coords VARCHAR(100) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        ''')

        # 4. reports
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INT AUTO_INCREMENT PRIMARY KEY,
                analysis_id INT,
                report_path VARCHAR(512) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (analysis_id) REFERENCES Analysis_History(id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        ''')

        # 5. activity_logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                action VARCHAR(100) NOT NULL,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        ''')

        # 6. Email_Notifications
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Email_Notifications (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                analysis_id INT,
                email VARCHAR(100) NOT NULL,
                delivery_status ENUM('SENT', 'FAILED') NOT NULL,
                error_message TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (analysis_id) REFERENCES Analysis_History(id) ON DELETE CASCADE
            ) ENGINE=InnoDB
        ''')

        conn.commit()
        self._seed_default_users(cursor, conn)
        conn.close()

    def _seed_default_users(self, cursor, conn):
        """Seeds default Admin and User credentials if counts are zero."""
        # Seed Admin
        try:
            cursor.execute("SELECT COUNT(*) FROM admins")
            admin_count = cursor.fetchone()[0]
        except Exception:
            admin_count = 0
            
        if admin_count == 0:
            admin_hash = generate_password_hash('adminpassword')
            if self.engine == 'sqlite':
                cursor.execute("INSERT INTO admins (username, password_hash) VALUES (?, ?)", 
                               ('admin', admin_hash))
            else:
                cursor.execute("INSERT INTO admins (username, password_hash) VALUES (%s, %s)", 
                               ('admin', admin_hash))
            conn.commit()
            print("[Database Manager] Seeded Default Admin Account. admin/adminpassword")
            
        # Seed User
        try:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
        except Exception:
            user_count = 0
            
        if user_count == 0:
            user_hash = generate_password_hash('userpassword')
            if self.engine == 'sqlite':
                cursor.execute("INSERT INTO users (full_name, email, password_hash, status) VALUES (?, ?, ?, ?)", 
                               ('Default User', 'user@example.com', user_hash, 'ACTIVE'))
            else:
                cursor.execute("INSERT INTO users (full_name, email, password_hash, status) VALUES (%s, %s, %s, %s)", 
                               ('Default User', 'user@example.com', user_hash, 'ACTIVE'))
            conn.commit()
            print("[Database Manager] Seeded Default User Account. user@example.com/userpassword")

db = DatabaseManager()
