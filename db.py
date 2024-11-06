import sqlite3
from datetime import datetime

def initialize_database(db_path="queries.db"):
    """
    Initialize the SQLite database with WAL mode and create the queries table
    """
    # Connect to the database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    
    # Enable WAL mode
    cursor.execute('PRAGMA journal_mode=WAL')
    
    # Create the queries table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS queries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input TEXT NOT NULL,
        output TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
    
    print(f"database '{db_path}' created successfully")

def add_query(input_text: str, output_text: str, db_path="queries.db"):
    """
    Add a new query to the database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO queries (input, output)
    VALUES (?, ?)
    ''', (input_text, output_text))
    
    conn.commit()
    conn.close()
    print("wrote query to db...")