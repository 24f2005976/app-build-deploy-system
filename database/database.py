import sqlite3
import json
from datetime import datetime
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path="evaluation.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tasks table - stores tasks sent to students
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email TEXT NOT NULL,
                task TEXT NOT NULL,
                round INTEGER NOT NULL,
                nonce TEXT NOT NULL,
                brief TEXT NOT NULL,
                attachments TEXT,  -- JSON string
                checks TEXT,       -- JSON string
                evaluation_url TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                statuscode INTEGER,
                secret TEXT NOT NULL,
                UNIQUE(email, task, round)
            )
        ''')
        
        # Repos table - stores repo submissions from students
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS repos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email TEXT NOT NULL,
                task TEXT NOT NULL,
                round INTEGER NOT NULL,
                nonce TEXT NOT NULL,
                repo_url TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                pages_url TEXT NOT NULL,
                UNIQUE(email, task, round)
            )
        ''')
        
        # Results table - stores evaluation results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email TEXT NOT NULL,
                task TEXT NOT NULL,
                round INTEGER NOT NULL,
                repo_url TEXT NOT NULL,
                commit_sha TEXT NOT NULL,
                pages_url TEXT NOT NULL,
                check_name TEXT NOT NULL,
                score REAL NOT NULL,
                reason TEXT,
                logs TEXT
            )
        ''')
        
        # Submissions table - stores student submissions from Google Form
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                email TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                secret TEXT NOT NULL,
                repo_url TEXT,
                UNIQUE(email)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def insert_task(self, task_data):
        """Insert a new task record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tasks 
                (timestamp, email, task, round, nonce, brief, attachments, checks, 
                 evaluation_url, endpoint, statuscode, secret)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                task_data['email'],
                task_data['task'],
                task_data['round'],
                task_data['nonce'],
                task_data['brief'],
                json.dumps(task_data.get('attachments', [])),
                json.dumps(task_data.get('checks', [])),
                task_data['evaluation_url'],
                task_data['endpoint'],
                task_data.get('statuscode'),
                task_data['secret']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting task: {e}")
            return False
        finally:
            conn.close()
    
    def insert_repo(self, repo_data):
        """Insert a new repo submission"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO repos 
                (timestamp, email, task, round, nonce, repo_url, commit_sha, pages_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                repo_data['email'],
                repo_data['task'],
                repo_data['round'],
                repo_data['nonce'],
                repo_data['repo_url'],
                repo_data['commit_sha'],
                repo_data['pages_url']
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting repo: {e}")
            return False
        finally:
            conn.close()
    
    def insert_result(self, result_data):
        """Insert a new evaluation result"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO results 
                (timestamp, email, task, round, repo_url, commit_sha, pages_url, 
                 check_name, score, reason, logs)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                result_data['email'],
                result_data['task'],
                result_data['round'],
                result_data['repo_url'],
                result_data['commit_sha'],
                result_data['pages_url'],
                result_data['check_name'],
                result_data['score'],
                result_data.get('reason', ''),
                result_data.get('logs', '')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting result: {e}")
            return False
        finally:
            conn.close()
    
    def get_tasks(self, email=None, round_num=None):
        """Get tasks, optionally filtered by email and round"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM tasks WHERE 1=1"
        params = []
        
        if email:
            query += " AND email = ?"
            params.append(email)
        
        if round_num:
            query += " AND round = ?"
            params.append(round_num)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_repos(self, email=None, round_num=None):
        """Get repo submissions, optionally filtered by email and round"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM repos WHERE 1=1"
        params = []
        
        if email:
            query += " AND email = ?"
            params.append(email)
        
        if round_num:
            query += " AND round = ?"
            params.append(round_num)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def get_results(self, email=None, task=None):
        """Get evaluation results, optionally filtered by email and task"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM results WHERE 1=1"
        params = []
        
        if email:
            query += " AND email = ?"
            params.append(email)
        
        if task:
            query += " AND task = ?"
            params.append(task)
        
        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    def task_exists(self, email, task, round_num):
        """Check if a task already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM tasks 
            WHERE email = ? AND task = ? AND round = ?
        ''', (email, task, round_num))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def repo_exists(self, email, task, round_num):
        """Check if a repo submission already exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM repos 
            WHERE email = ? AND task = ? AND round = ?
        ''', (email, task, round_num))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0
    
    def insert_submission(self, submission_data):
        """Insert a new submission from Google Form"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO submissions 
                (timestamp, email, endpoint, secret, repo_url)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                submission_data['email'],
                submission_data['endpoint'],
                submission_data['secret'],
                submission_data.get('repo_url', '')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error inserting submission: {e}")
            return False
        finally:
            conn.close()
    
    def get_submissions(self):
        """Get all submissions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM submissions")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]

if __name__ == "__main__":
    # Test the database
    db = DatabaseManager()
    print("Database initialized successfully!")