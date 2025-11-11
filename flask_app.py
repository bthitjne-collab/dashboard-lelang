# flask_app.py
import datetime
from flask import Flask, request, session, redirect, url_for, render_template_string, flash
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_db, get_connection

# Inisialisasi DB
init_db()

app = Flask(__name__)
app.secret_key = "ganti-dengan-secret-key-unik"  # ganti ke secret aman untuk produksi

# ----------------------
# Helper / util database
# ----------------------
def db_conn():
    conn = get_connection()
    try:
        conn.execute("PRAGMA foreign_keys = ON")
    except Exception:
        pass
    return conn

def current_user():
    return session.get("username")

def is_admin():
    return session.get("role") == "admin"

def tambah_aktivitas(username, aksi):
    conn = db_conn()
    c = conn.cursor()
    c.execute("INSERT INTO aktivitas (username, aksi) VALUES (?, ?)", (username, aksi))
    conn.commit()
    conn.close()

def cek_pemenang_otomatis():
    conn = db_conn()
    c = conn.cursor()
    now = datetime.datetime.now()
    c.execute("SELECT id_barang, nama_barang FROM barang WHERE waktu_selesai <= ? AND status='aktif'", (now,))
    barang_selesai = c.fetchall()
    hasil_list = []
    for (id_barang, nama_barang) in barang_selesai:
        # ambil penawaran tertinggi (username, harga)
        c.execute("SELECT username, harga_tawar FROM penawaran WHERE id_barang=? ORDER BY harga_tawar DESC LIMIT 1", (id_barang,))
        winner = c.fetchone()
        if winner:
            pembeli, harga_tertinggi = winner
            c.execute("INSERT INTO penjualan (id_barang, tanggal, harga_terjual, pembeli) VALUES (?, ?, ?, ?)",
                      (id_barang, now.date(), harga_tertinggi, pembeli))
            c.execute("UPDATE barang SET status='terjual' WHERE id_barang=?", (id_barang,))
            tambah_aktivitas(pembeli, f"Menang lelang '{nama_barang}' dengan harga Rp{harga_tertinggi}")
            hasil_list.append((nama_barang, pembeli, harga_tertinggi))
        else:
            c.execute("UPDATE barang SET status='gagal' WHERE id_barang=?", (id_barang,))
            hasil_list.append((nama_barang, None, None))
    conn.commit()
    conn.close()
    return hasil_list

# ----------------------
# Routes: Auth
# ----------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        email = request.form.get("email", "").strip()
        if not username or not password:
            flash("Username & password wajib diisi.", "danger")
            return redirect(url_for("register"))

        conn = db_conn()
        c = conn.cursor()
        # cek exist
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if c.fetchone():
            flash("Username sudah terpakai.", "warning")
            conn.close()
            return redirect(url_for("register"))

        pw_hash = generate_password_hash(password)
        c.execute("INSERT INTO users (username, password, email, role, status) VALUES (?, ?, ?, ?, ?)",
                  (username, pw_hash, email, "user", "aktif"))
        conn.commit()
        conn.close()
        tambah_aktivitas(username, "Registrasi akun")
        flash("Registrasi berhasil. Silakan login.", "success")
        return redirect(url_for("login"))

    return render_template_string(REG_TEMPLATE, current_user=current_user())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        conn = db_conn()
        c = conn.cursor()
        c.execute("SELECT password, role FROM users WHERE username=?", (username,))
        row = c.fetchone()
        conn.close()
        if not row:
            flash("User tidak ditemukan.", "danger")
            return redirect(url_for("login"))
        pw_hash, role = row
        if check_password_hash(pw_hash, password):
            session["username"] = username
            session["role"] = role
            tambah_aktivitas(username, "Login")
            flash(f"Selamat datang, {username}!", "success")
            return redirect(url_for("index"))
        else:
            flash("Password salah.", "danger")
            return redirect(url_for("login"))

    return render_template_string(LOGIN_TEMPLATE, current_user=current_user())

@app.route("/logout")
def logout():
    user = current_user()
    session.clear()
    if user:
        tambah_aktivitas(user, "Logout")
    flash("Anda telah logout.", "info")
    return redirect(url_for("index"))

# ----------------------
# Routes: Main / Lelang
# ----------------------
@app.route("/")
def index():
    conn = db_conn()
    c = conn.cursor()
    # tampilkan barang aktif
    now = datetime.datetime.now()
    c.execute("""SELECT id_barang, nama_barang, kategori, harga_awal, penjual, waktu_mulai, waktu_selesai, status, gambar
                 FROM barang
                 WHERE status='aktif'""")
    items = c.fetchall()

    # ambil top 3 aktivitas terakhir
    c.execute("SELECT username, aksi, waktu FROM aktivitas ORDER BY waktu DESC LIMIT 5")
    logs = c.fetchall()
    conn.close()
    return render_template_string(INDEX_TEMPLATE, items=items, logs=logs, current_user=current_user(), is_admin=is_admin(), now=now)

@app.route("/item/<int:id_barang>")
def item_view(id_barang):
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM barang WHERE id_barang=?", (id_barang,))
    item = c.fetchone()
    if not item:
        conn.close()
        flash("Barang tidak ditemukan.", "danger")
        return redirect(url_for("index"))

    # daftar penawaran untuk item ini
    c.execute("SELECT username, harga_tawar, waktu FROM penawaran WHERE id_barang=? ORDER BY harga_tawar DESC", (id_barang,))
    bids = c.fetchall()
    conn.close()
    return render_template_string(ITEM_TEMPLATE, item=item, bids=bids, current_user=current_user())

@app.route("/add_item", methods=["GET", "POST"])
def add_item():
    if not current_user():
        flash("Silakan login untuk menambah barang.", "warning")
        return redirect(url_for("login"))
    if request.method == "POST":
        nama = request.form["nama"].strip()
        kategori = request.form.get("kategori", "").strip()
        harga_awal = int(request.form.get("harga_awal", 0))
        durasi = int(request.form.get("durasi", 60))
        gambar = request.form.get("gambar", "").strip()
        penjual = current_user()

        waktu_mulai = datetime.datetime.now()
        waktu_selesai = waktu_mulai + datetime.timedelta(minutes=durasi)
        conn = db_conn()
        c = conn.cursor()
        c.execute("""INSERT INTO barang (nama_barang, kategori, harga_awal, penjual, waktu_mulai, waktu_selesai, gambar)
                     VALUES (?, ?, ?, ?, ?, ?, ?)""", (nama, kategori, harga_awal, penjual, waktu_mulai, waktu_selesai, gambar))
        conn.commit()
        conn.close()
        tambah_aktivitas(penjual, f"Menambahkan barang '{nama}' (durasi {durasi} menit)")
        flash("Barang berhasil ditambahkan.", "success")
        return redirect(url_for("index"))

    return render_template_string(ADD_ITEM_TEMPLATE, current_user=current_user())

@app.route("/bid", methods=["POST"])
def bid():
    if not current_user():
        flash("Silakan login dulu untuk menawar.", "warning")
        return redirect(url_for("login"))
    id_barang = int(request.form["id_barang"])
    harga = int(request.form["harga"])
    username = current_user()

    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT nama_barang, harga_awal, status FROM barang WHERE id_barang=?", (id_barang,))
    b = c.fetchone()
    if not b:
        conn.close()
        flash("Barang tidak ditemukan.", "danger")
        return redirect(url_for("index"))
    if b[2] != "aktif":
        conn.close()
        flash("Lelang sudah tidak aktif.", "warning")
        return redirect(url_for("index"))

    # cek penawaran tertinggi
    c.execute("SELECT MAX(harga_tawar) FROM penawaran WHERE id_barang=?", (id_barang,))
    max_tawar = c.fetchone()[0] or 0
    if harga <= max(b[1], max_tawar):
        conn.close()
        flash(f"Tawaran harus lebih besar dari Rp{max(b[1], max_tawar)}.", "danger")
        return redirect(url_for("item_view", id_barang=id_barang))

    c.execute("INSERT INTO penawaran (id_barang, username, harga_tawar) VALUES (?, ?, ?)", (id_barang, username, harga))
    conn.commit()
    conn.close()
    tambah_aktivitas(username, f"Menawar Rp{harga} pada barang #{id_barang}")
    flash("Tawaran berhasil dikirim.", "success")
    return redirect(url_for("item_view", id_barang=id_barang))

# ----------------------
# Admin routes
# ----------------------
@app.route("/admin")
def admin_dashboard():
    if not is_admin():
        flash("Butuh akses admin.", "danger")
        return redirect(url_for("index"))
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM barang WHERE status='aktif'")
    aktif = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM penjualan")
    terjual = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM penawaran")
    tot_penawaran = c.fetchone()[0]
    conn.close()
    return render_template_string(ADMIN_TEMPLATE, total_users=total_users, aktif=aktif, terjual=terjual, tot_penawaran=tot_penawaran)

@app.route("/admin/process_winners")
def admin_process_winners():
    if not is_admin():
        flash("Butuh akses admin.", "danger")
        return redirect(url_for("index"))
    hasil = cek_pemenang_otomatis()
    if not hasil:
        flash("Tidak ada lelang yang perlu diproses saat ini.", "info")
    else:
        for nama_barang, pembeli, harga in hasil:
            if pembeli:
                flash(f"🏆 {nama_barang} dimenangkan oleh {pembeli} (Rp{harga})", "success")
            else:
                flash(f"⚠️ {nama_barang} tidak ada penawar -> gagal terjual.", "warning")
    return redirect(url_for("admin_dashboard"))

# ----------------------
# Aktivitas dan penjualan
# ----------------------
@app.route("/aktivitas")
def aktivitas():
    conn = db_conn()
    c = conn.cursor()
    c.execute("SELECT username, aksi, waktu FROM aktivitas ORDER BY waktu DESC LIMIT 50")
    logs = c.fetchall()
    conn.close()
    return render_template_string(ACTIVITY_TEMPLATE, logs=logs)

@app.route("/penjualan")
def penjualan():
    conn = db_conn()
    c = conn.cursor()
    c.execute("""SELECT p.id_penjualan, b.nama_barang, p.tanggal, p.harga_terjual, p.pembeli
                 FROM penjualan p
                 LEFT JOIN barang b ON p.id_barang=b.id_barang
                 ORDER BY p.tanggal DESC LIMIT 100""")
    rows = c.fetchall()
    conn.close()
    return render_template_string(SALES_TEMPLATE, rows=rows)

# ----------------------
# Minimal templates (inline)
# ----------------------
# For produksi, pindahkan ke folder templates/ dan pakai render_template
BASE_HTML = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Mini Lelang</title>
  <style>
    body{font-family: Arial, sans-serif; max-width:1000px;margin:20px auto;padding:10px}
    nav{display:flex;gap:10px;margin-bottom:10px}
    .box{border:1px solid #ddd;padding:12px;border-radius:8px;margin-bottom:12px}
    .success{color:green}.danger{color:red}.warning{color:orange}
    .item{padding:8px;border-bottom:1px solid #eee}
    .small{font-size:0.9rem;color:#666}
    form input, form select {padding:6px;margin:4px 0;}
  </style>
</head>
<body>
  <nav>
    <a href="{{ url_for('index') }}">Beranda</a>
    <a href="{{ url_for('aktivitas') }}">Aktivitas</a>
    <a href="{{ url_for('penjualan') }}">Penjualan</a>
    {% if current_user %}
      <strong>{{ current_user }}</strong>
      <a href="{{ url_for('add_item') }}">Tambah Barang</a>
      <a href="{{ url_for('logout') }}">Logout</a>
    {% else %}
      <a href="{{ url_for('login') }}">Login</a>
      <a href="{{ url_for('register') }}">Register</a>
    {% endif %}
    {% if is_admin %}
      <a href="{{ url_for('admin_dashboard') }}">Admin</a>
    {% endif %}
  </nav>
  {% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
      <div class="box">
      {% for category, msg in messages %}
        <div class="{{ 'danger' if category=='danger' else 'success' if category=='success' else 'warning' if category=='warning' else '' }}">{{ msg }}</div>
      {% endfor %}
      </div>
    {% endif %}
  {% endwith %}

  {% block content %}{% endblock %}
</body>
</html>
"""

REG_TEMPLATE = BASE_HTML + """
{% block content %}
<div class="box">
  <h3>Register</h3>
  <form method="post">
    <label>Username</label><br><input name="username" required><br>
    <label>Password</label><br><input name="password" type="password" required><br>
    <label>Email</label><br><input name="email"><br>
    <button type="submit">Register</button>
  </form>
</div>
{% endblock %}
"""

LOGIN_TEMPLATE = BASE_HTML + """
{% block content %}
<div class="box">
  <h3>Login</h3>
  <form method="post">
    <label>Username</label><br><input name="username" required><br>
    <label>Password</label><br><input name="password" type="password" required><br>
    <button type="submit">Login</button>
  </form>
</div>
{% endblock %}
"""

INDEX_TEMPLATE = BASE_HTML + """
{% block content %}
<h2>Barang Lelang Aktif</h2>
<div class="box">
  {% if not items %}
    <div>Tidak ada barang aktif saat ini.</div>
  {% else %}
    {% for it in items %}
      <div class="item">
        <strong><a href="{{ url_for('item_view', id_barang=it[0]) }}">{{ it[1] }}</a></strong>
        <div class="small">Kategori: {{ it[2] }} — Harga Awal: Rp{{ it[3] }} — Penjual: {{ it[4] }}</div>
        <div class="small">Selesai: {{ it[6] }}</div>
      </div>
    {% endfor %}
  {% endif %}
</div>

<h3>Aktivitas Terakhir</h3>
<div class="box">
  {% for l in logs %}
    <div class="small">{{ l[2] }} — {{ l[0] }}: {{ l[1] }}</div>
  {% endfor %}
</div>
{% endblock %}
"""

ITEM_TEMPLATE = BASE_HTML + """
{% block content %}
<div class="box">
  <h3>{{ item[1] }} {% if item[8] %}<img src="{{ item[8] }}" style="height:40px;">{% endif %}</h3>
  <div class="small">Penjual: {{ item[5] }} | Kategori: {{ item[3] }}</div>
  <div class="small">Harga Awal: Rp{{ item[4] }}</div>
  <div class="small">Waktu Mulai: {{ item[6] }} | Waktu Selesai: {{ item[7] }}</div>
  {% if current_user %}
    <form method="post" action="{{ url_for('bid') }}">
      <input type="hidden" name="id_barang" value="{{ item[0] }}">
      <label>Masukkan Tawaran (Rp)</label><br>
      <input name="harga" type="number" required>
      <button type="submit">Kirim Tawaran</button>
    </form>
  {% else %}
    <div class="small">Login untuk menawar.</div>
  {% endif %}
</div>

<div class="box">
  <h4>Penawaran</h4>
  {% if not bids %}
    <div>Tidak ada penawaran.</div>
  {% else %}
    {% for b in bids %}
      <div class="small">{{ b[2] }} — {{ b[0] }}: Rp{{ b[1] }}</div>
    {% endfor %}
  {% endif %}
</div>
{% endblock %}
"""

ADD_ITEM_TEMPLATE = BASE_HTML + """
{% block content %}
<div class="box">
  <h3>Tambah Barang Lelang</h3>
  <form method="post">
    <label>Nama Barang</label><br><input name="nama" required><br>
    <label>Kategori</label><br><input name="kategori"><br>
    <label>Harga Awal (Rp)</label><br><input name="harga_awal" type="number" required><br>
    <label>Durasi (menit)</label><br><input name="durasi" type="number" value="60"><br>
    <label>URL Gambar (opsional)</label><br><input name="gambar"><br>
    <button type="submit">Tambah</button>
  </form>
</div>
{% endblock %}
"""

ADMIN_TEMPLATE = BASE_HTML + """
{% block content %}
<div class="box">
  <h3>Admin Dashboard</h3>
  <div>Total User: {{ total_users }}</div>
  <div>Barang Aktif: {{ aktif }}</div>
  <div>Terjual: {{ terjual }}</div>
  <div>Total Penawaran: {{ tot_penawaran }}</div>
  <div style="margin-top:10px;">
    <a href="{{ url_for('admin_process_winners') }}">Proses Pemenang Sekarang</a>
  </div>
</div>
{% endblock %}
"""

ACTIVITY_TEMPLATE = BASE_HTML + """
{% block content %}
<div class="box">
  <h3>Log Aktivitas</h3>
  {% for l in logs %}
    <div class="small">{{ l[2] }} — {{ l[0] }}: {{ l[1] }}</div>
  {% endfor %}
</div>
{% endblock %}
"""

SALES_TEMPLATE = BASE_HTML + """
{% block content %}
<div class="box">
  <h3>Riwayat Penjualan</h3>
  {% for r in rows %}
    <div class="small">{{ r[2] }} — {{ r[1] }} — Rp{{ r[3] }} — Pembeli: {{ r[4] }}</div>
  {% endfor %}
</div>
{% endblock %}
"""

# ----------------------
# Run app
# ----------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
