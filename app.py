conn = sqlite3.connect('lelang.db')

import streamlit as st
import pandas as pd
import sqlite3
import altair as alt

# Judul dashboard
st.title("📊 Dashboard Penjualan Lelang Barang")

# Koneksi ke database SQLite
conn = sqlite3.connect('lelang.db')
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
    .mark_bar()
    .encode(x='bulan', y='harga_terjual', tooltip=['bulan', 'harga_terjual'])
    .properties(title='Total Penjualan per Bulan')
)
st.altair_chart(chart, use_container_width=True)

# Tabel Barang & Penjualan
st.subheader("📦 Daftar Barang")
st.dataframe(barang)

st.subheader("💰 Daftar Penjualan")
st.dataframe(penjualan)
