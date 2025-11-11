import datetime
from database import get_connection, init_db

# Jalankan inisialisasi database sekali
init_db()

# === Utility: Tambah Aktivitas ===
def tambah_aktivitas(username, aksi):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO aktivitas (username, aksi) VALUES (?, ?)", (username, aksi))
    conn.commit()
    conn.close()


# === Tambah Barang (oleh admin / penjual) ===
def tambah_barang(nama, kategori, harga_awal, penjual, durasi_menit):
    conn = get_connection()
    c = conn.cursor()
    waktu_mulai = datetime.datetime.now()
    waktu_selesai = waktu_mulai + datetime.timedelta(minutes=durasi_menit)
    c.execute("""
        INSERT INTO barang (nama_barang, kategori, harga_awal, penjual, waktu_mulai, waktu_selesai)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (nama, kategori, harga_awal, penjual, waktu_mulai, waktu_selesai))
    conn.commit()
    conn.close()
    tambah_aktivitas(penjual, f"Menambahkan barang '{nama}' untuk dilelang.")
    print(f"✅ Barang '{nama}' berhasil ditambahkan! (Berakhir: {waktu_selesai})")


# === Tampilkan Daftar Barang Aktif ===
def tampilkan_barang():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id_barang, nama_barang, kategori, harga_awal, penjual, waktu_selesai FROM barang WHERE status='aktif'")
    data = c.fetchall()
    conn.close()
    if not data:
        print("⚠️  Belum ada barang yang dilelang.")
    else:
        print("\n📦 Daftar Barang Aktif:")
        for row in data:
            print(f"[{row[0]}] {row[1]} | Kategori: {row[2]} | Harga Awal: Rp{row[3]} | Penjual: {row[4]} | Selesai: {row[5]}")
    print()


# === Ajukan Penawaran ===
def ajukan_penawaran(id_barang, username, harga_tawar):
    conn = get_connection()
    c = conn.cursor()

    # Cek apakah barang masih aktif
    c.execute("SELECT nama_barang, harga_awal, status FROM barang WHERE id_barang=?", (id_barang,))
    b = c.fetchone()
    if not b:
        print("❌ Barang tidak ditemukan.")
        return
    if b[2] != "aktif":
        print("❌ Barang sudah tidak aktif.")
        return

    # Cek harga penawaran tertinggi saat ini
    c.execute("SELECT MAX(harga_tawar) FROM penawaran WHERE id_barang=?", (id_barang,))
    max_tawar = c.fetchone()[0] or 0
    if harga_tawar <= max(b[1], max_tawar):
        print(f"❌ Tawaran harus lebih tinggi dari harga awal / penawaran tertinggi (Rp{max(b[1], max_tawar)}).")
        return

    # Simpan penawaran
    c.execute("INSERT INTO penawaran (id_barang, username, harga_tawar) VALUES (?, ?, ?)", (id_barang, username, harga_tawar))
    conn.commit()
    conn.close()
    tambah_aktivitas(username, f"Menawar Rp{harga_tawar} pada barang #{id_barang}")
    print(f"✅ Penawaran Rp{harga_tawar} berhasil disimpan!")


# === Cek & Umumkan Pemenang Otomatis ===
def cek_pemenang_otomatis():
    conn = get_connection()
    c = conn.cursor()
    now = datetime.datetime.now()

    c.execute("SELECT id_barang, nama_barang FROM barang WHERE waktu_selesai <= ? AND status='aktif'", (now,))
    barang_selesai = c.fetchall()

    for (id_barang, nama_barang) in barang_selesai:
        c.execute("SELECT username, MAX(harga_tawar) FROM penawaran WHERE id_barang=?", (id_barang,))
        hasil = c.fetchone()
        if hasil and hasil[0]:
            pembeli, harga_tertinggi = hasil
            c.execute("""
                INSERT INTO penjualan (id_barang, tanggal, harga_terjual, pembeli)
                VALUES (?, ?, ?, ?)
            """, (id_barang, now.date(), harga_tertinggi, pembeli))
            c.execute("UPDATE barang SET status='terjual' WHERE id_barang=?", (id_barang,))
            tambah_aktivitas(pembeli, f"Menang lelang '{nama_barang}' dengan harga Rp{harga_tertinggi}")
            print(f"🏆 Barang '{nama_barang}' dimenangkan oleh {pembeli} dengan harga Rp{harga_tertinggi}")
        else:
            c.execute("UPDATE barang SET status='gagal' WHERE id_barang=?", (id_barang,))
            print(f"⚠️ Barang '{nama_barang}' gagal terjual (tidak ada penawaran).")

    conn.commit()
    conn.close()


# === Tampilkan Aktivitas User ===
def tampilkan_aktivitas():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, aksi, waktu FROM aktivitas ORDER BY waktu DESC LIMIT 10")
    logs = c.fetchall()
    conn.close()

    print("\n📝 Log Aktivitas Terbaru:")
    for row in logs:
        print(f"{row[2]} | {row[0]} → {row[1]}")
    print()


# === Menu Utama CLI ===
def menu():
    while True:
        print("\n=== SISTEM LELANG OTOMATIS ===")
        print("1. Tambah Barang Lelang")
        print("2. Lihat Barang Aktif")
        print("3. Ajukan Penawaran")
        print("4. Cek & Umumkan Pemenang")
        print("5. Lihat Aktivitas")
        print("0. Keluar")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            nama = input("Nama Barang: ")
            kategori = input("Kategori: ")
            harga = int(input("Harga Awal: "))
            penjual = input("Nama Penjual: ")
            durasi = int(input("Durasi (menit): "))
            tambah_barang(nama, kategori, harga, penjual, durasi)
        elif pilihan == "2":
            tampilkan_barang()
        elif pilihan == "3":
            tampilkan_barang()
            idb = int(input("Masukkan ID Barang: "))
            user = input("Nama Anda: ")
            harga = int(input("Masukkan Harga Tawaran: "))
            ajukan_penawaran(idb, user, harga)
        elif pilihan == "4":
            cek_pemenang_otomatis()
        elif pilihan == "5":
            tampilkan_aktivitas()
        elif pilihan == "0":
            print("👋 Terima kasih! Program selesai.")
            break
        else:
            print("❌ Pilihan tidak valid.")


if __name__ == "__main__":
    menu()
