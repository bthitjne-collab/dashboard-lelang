import sqlite3
from sqlite3 import Connection

DB_PATH = "lelang.db"

def get_connection() -> Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # === Tabel Users ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT
    )
    """)

    # === Tabel Barang ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS barang (
        id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_barang TEXT,
        kategori TEXT,
        harga_awal INTEGER,
        status TEXT
    )
    """)

    # === Tabel Penjualan ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS penjualan (
        id_penjualan INTEGER PRIMARY KEY AUTOINCREMENT,
        id_barang INTEGER,
        tanggal DATE,
        harga_terjual INTEGER,
        pembeli TEXT
    )
    """)

    # Tambah user default kalau belum ada
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin123", "admin")
        )

    conn.commit()
    conn.close()
