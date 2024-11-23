import sqlite3


def initialize_database():
    conn = sqlite3.connect('app_tracker.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_time TEXT,
            end_time TEXT,
            total_time TEXT,
            results TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("База данных и таблица инициализированы.")