from flask import Flask, render_template, request, redirect, url_for, session, flash
import hashlib
from database import get_connection, init_db
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

init_db()

# ==========================
# 🔐 LOGIN & LOGOUT
# ==========================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user"] = user[1]
            session["role"] = user[5]
            if user[5] == "admin":
                return redirect(url_for("dashboard_admin"))
            else:
                return redirect(url_for("dashboard_user"))
        else:
            flash("Username atau password salah!", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ==========================
# 🧑 DASHBOARD ADMIN
# ==========================
@app.route("/admin")
def dashboard_admin():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM barang")
    barang = c.fetchall()
    conn.close()

    return render_template("dashboard_admin.html", barang=barang, user=session["user"])

# Tambah Barang
@app.route("/admin/add_item", methods=["POST"])
def add_item():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    nama = request.form["nama_barang"]
    kategori = request.form["kategori"]
    harga = request.form["harga_awal"]
    waktu_mulai = datetime.now()
    waktu_selesai = datetime.now().replace(hour=datetime.now().hour + 1)
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO barang (nama_barang, kategori, harga_awal, penjual, waktu_mulai, waktu_selesai) VALUES (?, ?, ?, ?, ?, ?)",
        (nama, kategori, harga, session["user"], waktu_mulai, waktu_selesai)
    )
    conn.commit()
    conn.close()
    flash("Barang berhasil ditambahkan!", "success")
    return redirect(url_for("dashboard_admin"))


# ==========================
# 🔑 ADMIN GANTI PASSWORD
# ==========================
@app.route("/admin/change_password", methods=["GET", "POST"])
def change_password():
    if "user" not in session or session["role"] != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"]
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT password FROM users WHERE username=?", (session["user"],))
        current_pw = c.fetchone()[0]

        if hashlib.sha256(old.encode()).hexdigest() != current_pw:
            flash("Password lama salah!", "error")
        else:
            hashed = hashlib.sha256(new.encode()).hexdigest()
            c.execute("UPDATE users SET password=? WHERE username=?", (hashed, session["user"]))
            conn.commit()
            flash("Password berhasil diubah!", "success")
        conn.close()
    return render_template("change_password.html", user=session["user"])

# ==========================
# 🧍 DASHBOARD USER
# ==========================
@app.route("/user")
def dashboard_user():
    if "user" not in session or session["role"] != "user":
        return redirect(url_for("login"))

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM barang WHERE status='aktif'")
    barang = c.fetchall()
    conn.close()

    return render_template("dashboard_user.html", barang=barang, user=session["user"])


if __name__ == "__main__":
    app.run(debug=True)
