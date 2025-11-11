import sqlite3
from sqlite3 import Connection

DB_PATH = "lelang.db"

def get_connection() -> Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # === USERS (User System Lengkap) ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        email TEXT,
        saldo INTEGER DEFAULT 0,
        role TEXT,
        status TEXT DEFAULT 'aktif'
    )
    """)

    # === BARANG (Item yang Dilelang) ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS barang (
        id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_barang TEXT,
        kategori TEXT,
        harga_awal INTEGER,
        penjual TEXT,
        status TEXT DEFAULT 'aktif',
        waktu_mulai DATETIME,
        waktu_selesai DATETIME,
        gambar TEXT
    )
    """)

    # === PENAWARAN (Bidding System) ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS penawaran (
        id_penawaran INTEGER PRIMARY KEY AUTOINCREMENT,
        id_barang INTEGER,
        username TEXT,
        harga_tawar INTEGER,
        waktu DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # === PENJUALAN (Barang Terjual) ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS penjualan (
        id_penjualan INTEGER PRIMARY KEY AUTOINCREMENT,
        id_barang INTEGER,
        tanggal DATE,
        harga_terjual INTEGER,
        pembeli TEXT
    )
    """)

    # === AKTIVITAS (Log Aktivitas User) ===
    c.execute("""
    CREATE TABLE IF NOT EXISTS aktivitas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        aksi TEXT,
        waktu DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # === USER DEFAULT ADMIN ===
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users (username, password, email, role, status) VALUES (?, ?, ?, ?, ?)",
                  ("admin", "admin123", "admin@admin.com", "admin", "aktif"))

    conn.commit()
    conn.close()
