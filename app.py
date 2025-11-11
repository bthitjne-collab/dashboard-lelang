import streamlit as st
import pandas as pd
import altair as alt
from database import get_connection, init_db

st.set_page_config(page_title="Lelang Barang", layout="wide")

# === Inisialisasi Database ===
init_db()
conn = get_connection()

# === FUNGSI LOGIN & REGISTER ===
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
    except:
        return False

# === Session ===
if "user" not in st.session_state:
    st.session_state.user = None

# === LOGIN PAGE ===
if not st.session_state.user:
    st.title("🔐 Login ke Dashboard Lelang")
    tab1, tab2 = st.tabs(["Login", "Daftar Akun"])

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
        uname = st.text_input("Username Baru")
        upass = st.text_input("Password Baru", type="password")
        if st.button("Daftar"):
            if register_user(uname, upass):
                st.success("Akun berhasil dibuat, silakan login.")
            else:
                st.error("Username sudah digunakan.")
else:
    user = st.session_state.user
    st.sidebar.success(f"👤 {user[1]} ({user[3]})")
    if st.sidebar.button("🚪 Logout"):
        st.session_state.user = None
        st.rerun()

    menu = st.sidebar.radio("Navigasi", ["Dashboard", "Barang", "Penjualan", "Manajemen User"])

    # === DASHBOARD ===
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
            chart = alt.Chart(grafik).mark_bar(color="#1f77b4").encode(x='bulan', y='harga_terjual')
            st.altair_chart(chart, use_container_width=True)

    # === CRUD BARANG ===
    elif menu == "Barang":
        st.header("📦 Manajemen Barang")

        barang_df = pd.read_sql_query("SELECT * FROM barang", conn)
        st.dataframe(barang_df, use_container_width=True)

        st.subheader("➕ Tambah Barang Baru")
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

        st.subheader("📝 Edit / Hapus Barang")
        id_barang = st.number_input("Masukkan ID Barang", min_value=1, step=1)
        if st.button("Load Barang"):
            data = conn.execute("SELECT * FROM barang WHERE id_barang=?", (id_barang,)).fetchone()
            if data:
                nama_edit = st.text_input("Nama Barang", value=data[1])
                kategori_edit = st.text_input("Kategori", value=data[2])
                harga_edit = st.number_input("Harga Awal", min_value=0, value=data[3])
                status_edit = st.selectbox("Status", ["Dilelang", "Terjual"], index=0 if data[4]=="Dilelang" else 1)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Barang"):
                        conn.execute("""
                            UPDATE barang SET nama_barang=?, kategori=?, harga_awal=?, status=? WHERE id_barang=?
                        """, (nama_edit, kategori_edit, harga_edit, status_edit, id_barang))
                        conn.commit()
                        st.success("Barang berhasil diperbarui!")
                        st.rerun()
                with col2:
                    if st.button("Hapus Barang"):
                        conn.execute("DELETE FROM barang WHERE id_barang=?", (id_barang,))
                        conn.commit()
                        st.warning("Barang berhasil dihapus!")
                        st.rerun()
            else:
                st.error("Barang tidak ditemukan!")

    # === CRUD PENJUALAN ===
    elif menu == "Penjualan":
        st.header("💰 Manajemen Penjualan")
        penjualan_df = pd.read_sql_query("SELECT * FROM penjualan", conn)
        st.dataframe(penjualan_df, use_container_width=True)

        st.subheader("➕ Tambah Penjualan")
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

        st.subheader("📝 Edit / Hapus Penjualan")
        id_penjualan = st.number_input("Masukkan ID Penjualan", min_value=1, step=1)
        if st.button("Load Penjualan"):
            data = conn.execute("SELECT * FROM penjualan WHERE id_penjualan=?", (id_penjualan,)).fetchone()
            if data:
                id_barang_edit = st.number_input("ID Barang", min_value=1, value=data[1])
                tanggal_edit = st.date_input("Tanggal", pd.to_datetime(data[2]))
                harga_edit = st.number_input("Harga Terjual", min_value=0, value=data[3])
                pembeli_edit = st.text_input("Pembeli", value=data[4])
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Update Penjualan"):
                        conn.execute("""
                            UPDATE penjualan SET id_barang=?, tanggal=?, harga_terjual=?, pembeli=? WHERE id_penjualan=?
                        """, (id_barang_edit, tanggal_edit, harga_edit, pembeli_edit, id_penjualan))
                        conn.commit()
                        st.success("Penjualan berhasil diperbarui!")
                        st.rerun()
                with col2:
                    if st.button("Hapus Penjualan"):
                        conn.execute("DELETE FROM penjualan WHERE id_penjualan=?", (id_penjualan,))
                        conn.commit()
                        st.warning("Penjualan dihapus!")
                        st.rerun()
            else:
                st.error("Data penjualan tidak ditemukan!")

    # === CRUD USER ===
    elif menu == "Manajemen User":
        if user[3] != "admin":
            st.error("Hanya admin yang dapat mengakses halaman ini.")
        else:
            st.header("👥 Manajemen User")
            users_df = pd.read_sql_query("SELECT id, username, role FROM users", conn)
            st.dataframe(users_df, use_container_width=True)

            st.subheader("➕ Tambah User Baru")
            uname = st.text_input("Username")
            upass = st.text_input("Password", type="password")
            role = st.selectbox("Role", ["admin", "user"])
            if st.button("Tambah User"):
                if register_user(uname, upass, role):
                    st.success("User baru berhasil ditambahkan!")
                    st.rerun()
                else:
                    st.error("Username sudah digunakan.")

            st.subheader("📝 Edit / Hapus User")
            id_user = st.number_input("Masukkan ID User", min_value=1, step=1)
            if st.button("Load User"):
                data = conn.execute("SELECT * FROM users WHERE id=?", (id_user,)).fetchone()
                if data:
                    uname_edit = st.text_input("Username", value=data[1])
                    upass_edit = st.text_input("Password", value=data[2], type="password")
                    role_edit = st.selectbox("Role", ["admin", "user"], index=0 if data[3]=="admin" else 1)
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Update User"):
                            conn.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?",
                                         (uname_edit, upass_edit, role_edit, id_user))
                            conn.commit()
                            st.success("User berhasil diperbarui!")
                            st.rerun()
                    with col2:
                        if st.button("Hapus User"):
                            conn.execute("DELETE FROM users WHERE id=?", (id_user,))
                            conn.commit()
                            st.warning("User berhasil dihapus!")
                            st.rerun()
                else:
                    st.error("User tidak ditemukan!")
