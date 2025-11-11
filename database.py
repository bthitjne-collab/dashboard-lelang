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

    # === PENAWARAN ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS penawaran (
        id_penawaran INTEGER PRIMARY KEY AUTOINCREMENT,
        id_barang INTEGER,
        username TEXT,
        harga_tawar INTEGER,
        waktu DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()

# ==========================
# Helper functions
# ==========================
def add_barang(nama, kategori, harga, penjual, durasi_menit=60):
    conn = get_connection()
    c = conn.cursor()
    mulai = datetime.now()
    selesai = mulai + timedelta(minutes=durasi_menit)
    c.execute(
        "INSERT INTO barang (nama_barang, kategori, harga_awal, penjual, waktu_mulai, waktu_selesai) VALUES (?, ?, ?, ?, ?, ?)",
        (nama, kategori, harga, penjual, mulai, selesai)
    )
    conn.commit()
    conn.close()

def list_barang():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id_barang, nama_barang, kategori, harga_awal, penjual, status FROM barang")
    items = c.fetchall()
    conn.close()
    return items

def add_penawaran(id_barang, username, harga):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO penawaran (id_barang, username, harga_tawar) VALUES (?, ?, ?)",
              (id_barang, username, harga))
    conn.commit()
    conn.close()

def get_highest_bid(id_barang):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(harga_tawar) FROM penawaran WHERE id_barang=?", (id_barang,))
    row = c.fetchone()[0]
    conn.close()
    return row if row else 0

def get_bid_history(id_barang):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, harga_tawar, waktu FROM penawaran WHERE id_barang=? ORDER BY waktu DESC", (id_barang,))
    rows = c.fetchall()
    conn.close()
    return rows
