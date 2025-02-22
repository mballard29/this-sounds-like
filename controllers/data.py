import sqlite3

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def truncate_tables():
    conn = get_db_connection()
    conn.execute('DELETE FROM Albums;')
    conn.commit()
    conn.execute('DELETE FROM Tracks;')
    conn.commit()
    conn.execute('DELETE FROM Credits;')
    conn.commit()
    conn.close()