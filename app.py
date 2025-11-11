import streamlit as st
import pandas as pd
import altair as alt
import sqlite3
from database import get_connection, init_db

st.set_page_config(page_title="Lelang Barang", layout="wide")

# Inisialisasi DB
init_db()
conn = get_connection()

# === Login Section ===
def login_user(username, password):
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    return c.fetchone()

def register_user(username, password, role="user"):
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

# === Session State ===
if "user" not in st.session_state:
    st.session_state.user = None

# === Login Form ===
if not st.session_state.user:
    st.title("🔐 Login ke Dashboard Lelang")
    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = user
                st.success(f"Selamat datang, {username}!")
                st.rerun()
            else:
                st.error("Username atau password salah!")

    with tab2:
        new_user = st.text_input("Username Baru")
        new_pass = st.text_input("Password Baru", type="password")
        if st.button("Register"):
            if register_user(new_user, new_pass):
                st.success("User berhasil dibuat, silakan login.")
            else:
                st.error("Username sudah digunakan.")
else:
    user = st.session_state.user
    st.sidebar.success(f"Login sebagai: {user[1]} ({user[3]})")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

    # === Navigasi ===
    menu = st.sidebar.radio("Navigasi", ["Dashboard", "Barang", "Penjualan", "Manajemen User"])

    # === Dashboard ===
    if menu == "Dashboard":
        st.title("📊 Dashboard Penjualan Lelang Barang")

        barang = pd.read_sql_query("SELECT * FROM barang", conn)
        penjualan = pd.read_sql_query("SELECT * FROM penjualan", conn)

        total_barang = len(barang)
        terjual = penjualan['id_barang'].nunique()
        total_omzet = penjualan['harga_terjual'].sum() if len(penjualan) else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Barang", total_barang)
        col2.metric("Barang Terjual", terjual)
        col3.metric("Total Omzet", f"Rp {total_omzet:,.0f}")

        if not penjualan.empty:
            penjualan['tanggal'] = pd.to_datetime(penjualan['tanggal'])
            penjualan['bulan'] = penjualan['tanggal'].dt.to_period('M').astype(str)
            grafik = penjualan.groupby('bulan')['harga_terjual'].sum().reset_index()
            chart = alt.Chart(grafik).mark_bar().encode(x='bulan', y='harga_terjual')
            st.altair_chart(chart, use_container_width=True)

    # === CRUD Barang ===
    elif menu == "Barang":
        st.header("📦 Manajemen Barang")
        barang_df = pd.read_sql_query("SELECT * FROM barang", conn)
        st.dataframe(barang_df)

        st.subheader("Tambah Barang Baru")
        nama = st.text_input("Nama Barang")
        kategori = st.text_input("Kategori")
        harga = st.number_input("Harga Awal", min_value=0)
        status = st.selectbox("Status", ["Dilelang", "Terjual"])
        if st.button("Tambah Barang"):
            conn.execute("INSERT INTO barang (nama_barang, kategori, harga_awal, status) VALUES (?, ?, ?, ?)",
                         (nama, kategori, harga, status))
            conn.commit()
            st.success("Barang berhasil ditambahkan!")
            st.rerun()

    # === CRUD Penjualan ===
    elif menu == "Penjualan":
        st.header("💰 Manajemen Penjualan")
        penjualan_df = pd.read_sql_query("SELECT * FROM penjualan", conn)
        st.dataframe(penjualan_df)

        st.subheader("Tambah Transaksi Penjualan")
        id_barang = st.number_input("ID Barang", min_value=1)
        tanggal = st.date_input("Tanggal")
        harga_terjual = st.number_input("Harga Terjual", min_value=0)
        pembeli = st.text_input("Nama Pembeli")
        if st.button("Tambah Penjualan"):
            conn.execute("INSERT INTO penjualan (id_barang, tanggal, harga_terjual, pembeli) VALUES (?, ?, ?, ?)",
                         (id_barang, tanggal, harga_terjual, pembeli))
            conn.commit()
            st.success("Penjualan berhasil ditambahkan!")
            st.rerun()

    # === CRUD User (Admin Only) ===
    elif menu == "Manajemen User":
        if user[3] != "admin":
            st.error("Hanya admin yang boleh mengakses halaman ini.")
        else:
            st.header("👤 Manajemen User")
            users_df = pd.read_sql_query("SELECT id, username, role FROM users", conn)
            st.dataframe(users_df)

            st.subheader("Tambah User Baru")
