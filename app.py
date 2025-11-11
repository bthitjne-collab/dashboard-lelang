import streamlit as st
import hashlib
from database import get_connection, init_db, add_barang, list_barang, add_penawaran, get_highest_bid, get_bid_history
from datetime import datetime, timedelta

# Initialize DB
init_db()
st.set_page_config(page_title="Sistem Lelang", page_icon="💰")

# ==========================
# Helper
# ==========================
def hash_pass(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def check_login(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT password, role FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    if row and hash_pass(password) == row[0]:
        return row[1]
    return None

# ==========================
# Session State
# ==========================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = ""
    st.session_state.role = ""

# ==========================
# Login Form
# ==========================
if not st.session_state.logged_in:
    st.title("💰 Login Sistem Lelang")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            role = check_login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.session_state.role = role
                st.success(f"Login berhasil! Halo {username} ({role})")
            else:
                st.error("Username atau password salah.")

# ==========================
# Logout Sidebar
# ==========================
if st.session_state.logged_in:
    st.sidebar.write(f"Logged in sebagai: {st.session_state.user} ({st.session_state.role})")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = ""
        st.session_state.role = ""

# ==========================
# Admin Dashboard
# ==========================
if st.session_state.logged_in and st.session_state.role == "admin":
    st.title("🛠️ Dashboard Admin")

    st.subheader("Tambah Barang Baru")
    with st.form("add_barang_form"):
        nama = st.text_input("Nama Barang")
        kategori = st.text_input("Kategori")
        harga = st.number_input("Harga Awal", min_value=0)
        durasi = st.number_input("Durasi Lelang (menit)", min_value=1, value=60)
        submitted = st.form_submit_button("Tambah Barang")
        if submitted:
            add_barang(nama, kategori, harga, st.session_state.user, durasi)
            st.success(f"Barang '{nama}' berhasil ditambahkan!")

    st.subheader("Daftar Barang & Riwayat Penawaran")
    items = list_barang()
    for item in items:
        st.write(f"ID:{item[0]} | {item[1]} | Kategori: {item[2]} | Harga Awal: {item[3]} | Penjual: {item[4]} | Status: {item[5]}")
        history = get_bid_history(item[0])
        if history:
            for h in history:
                st.write(f"{h[0]} : {h[1]} ({h[2]})")
        else:
            st.write("Belum ada penawaran.")

    st.subheader("Ganti Password Admin")
    with st.form("change_pw_form"):
        old = st.text_input("Password Lama", type="password")
        new = st.text_input("Password Baru", type="password")
        submitted = st.form_submit_button("Ubah Password")
        if submitted:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT password FROM users WHERE username=?", (st.session_state.user,))
            current_pw = c.fetchone()[0]
            if hash_pass(old) != current_pw:
                st.error("Password lama salah!")
            else:
                c.execute("UPDATE users SET password=? WHERE username=?", (hash_pass(new), st.session_state.user))
                conn.commit()
                conn.close()
                st.success("Password berhasil diubah!")

# ==========================
# User Dashboard
# ==========================
if st.session_state.logged_in and st.session_state.role == "user":
    st.title("🛒 Dashboard User")
    st.subheader("Barang yang Dilelang")
    items = list_barang()
    for item in items:
        if item[5] == "aktif":
            st.write(f"ID:{item[0]} | {item[1]} | Kategori: {item[2]} | Harga Awal: {item[3]} | Penjual: {item[4]}")
            highest = get_highest_bid(item[0])
            st.write(f"💰 Tawaran tertinggi saat ini: {highest}")

            with st.form(f"bid_form_{item[0]}"):
                bid = st.number_input("Masukkan tawaran Anda", min_value=highest+1, step=1)
                submitted = st.form_submit_button("Tawar")
                if submitted:
                    add_penawaran(item[0], st.session_state.user, bid)
                    st.success(f"Tawaran {bid} berhasil dikirim!")

            st.write("Riwayat penawaran:")
            history = get_bid_history(item[0])
            for h in history:
                st.write(f"{h[0]} : {h[1]} ({h[2]})")
