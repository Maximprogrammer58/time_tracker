import logging
import sqlite3


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def initialize_database():
    try:
        conn = sqlite3.connect('app_tracker.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TEXT,
                end_time TEXT,
                total_time TEXT,
                results TEXT,
                visited_apps TEXT
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error initializing database: {e}")
    finally:
        conn.close()


def execute_query(query, params=(), fetch=True):
    try:
        conn = sqlite3.connect('app_tracker.db')
        cursor = conn.cursor()
        cursor.execute(query, params)
        if fetch:
            results = cursor.fetchall()
            return results
        else:
            conn.commit()
    except sqlite3.Error as e:
        logging.error(f"Error executing request: {e}")
    finally:
        conn.close()
