import sqlite3

def get_connection():
    return sqlite3.connect("users.db")

def init_iris_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS iris_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        embedding BLOB
    )
    """)
    conn.commit()
    conn.close()

def register_iris(name, iris_embedding):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO iris_users (name, embedding) VALUES (?, ?)",
        (name, iris_embedding.tobytes())
    )
    conn.commit()
    conn.close()

# 최초 테이블 생성 실행
init_iris_db()