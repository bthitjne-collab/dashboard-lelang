import streamlit as st
import pandas as pd
import sqlite3
import os
import altair as alt

st.set_page_config(page_title="Dashboard Lelang Barang", layout="wide")

# === Buat database SQLite dari nol di runtime (tidak pakai file GitHub) ===
DB_PATH = "lelang.db"

# Selalu buat database baru (supaya tidak error "file is not a database")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)

# Buat tabel
conn.execute("""
CREATE TABLE barang (
    id_barang INTEGER PRIMARY KEY AUTOINCREMENT,
    nama_barang TEXT,
    kategori TEXT,
    harga_awal INTEGER,
    status TEXT
)
""")
conn.execute("""
CREATE TABLE penjualan (
    id_penjualan INTEGER PRIMARY KEY AUTOINCREMENT,
    id_barang INTEGER,
    tanggal DATE,
    harga_terjual INTEGER,
    pembeli TEXT
)
""")

# Isi data contoh
barang_data = [
    ("Laptop ASUS", "Elektronik", 3500000, "Terjual"),
    ("Kamera Canon", "Elektronik", 2500000, "Dilelang"),
    ("Sepeda Gunung", "Olahraga", 1800000, "Terjual"),
]
penjualan_data = [
    (1, "2025-01-10", 4000000, "Andi"),
    (3, "2025-02-05", 2100000, "Budi"),
]

conn.executemany("INSERT INTO barang (nama_barang, kategori, harga_awal, status) VALUES (?, ?, ?, ?)", barang_data)
conn.executemany("INSERT INTO penjualan (id_barang, tanggal, harga_terjual, pembeli) VALUES (?, ?, ?, ?)", penjualan_data)
conn.commit()

# === Tampilkan Dashboard ===
st.title("📊 Dashboard Penjualan Lelang Barang")

barang = pd.read_sql_query("SELECT * FROM barang", conn)
penjualan = pd.read_sql_query("SELECT * FROM penjualan", conn)

# Statistik Ringkas
total_barang = len(barang)
terjual = penjualan['id_barang'].nunique()
total_omzet = penjualan['harga_terjual'].sum()

col1, col2, col3 = st.columns(3)
col1.metric("Total Barang", total_barang)
col2.metric("Barang Terjual", terjual)
col3.metric("Total Omzet", f"Rp {total_omzet:,.0f}")

# Grafik Penjualan per Bulan
penjualan['tanggal'] = pd.to_datetime(penjualan['tanggal'])
penjualan['bulan'] = penjualan['tanggal'].dt.to_period('M').astype(str)
grafik = penjualan.groupby('bulan')['harga_terjual'].sum().reset_index()

chart = (
    alt.Chart(grafik)
    .mark_bar(color="#1f77b4")
    .encode(x='bulan', y='harga_terjual', tooltip=['bulan', 'harga_terjual'])
    .properties(title='Total Penjualan per Bulan')
)
st.altair_chart(chart, use_container_width=True)

# Tabel Barang & Penjualan
st.subheader("📦 Daftar Barang")
st.dataframe(barang)

st.subheader("💰 Daftar Penjualan")
st.dataframe(penjualan)
