import sqlite3
from sqlite3 import Connection
from datetime import datetime

DB_PATH = "lelang.db"

def get_connection() -> Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # === USERS ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        role TEXT,
        status TEXT DEFAULT 'aktif'
    )
    """)

    # Default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        import hashlib
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        c.execute("INSERT INTO users (username, password, email, role, status) VALUES (?, ?, ?, ?, ?)",
                  ("admin", pw, "admin@admin.com", "admin", "aktif"))

    # === BARANG ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS barang (
        id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_barang TEXT,
        kategori TEXT,
        harga_awal INTEGER,
        penjual TEXT,
        status TEXT DEFAULT 'aktif',
        waktu_mulai DATETIME,
        waktu_selesai DATETIME
    )
    """)

    conn.commit()
    conn.close()
