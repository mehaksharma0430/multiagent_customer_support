import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "chat_history.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        bot_response TEXT
    )
    """)

    conn.commit()
    conn.close()


def save_chat(user_message, bot_response):
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO chats(user_message, bot_response)
    VALUES (?, ?)
    """, (user_message, bot_response))

    conn.commit()
    conn.close()


def get_chats():
    conn = get_conn()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, user_message, bot_response
    FROM chats
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "query": row[1],
            "response": row[2]
        }
        for row in rows
    ]