from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

def get_db():
    return sqlite3.connect("database.db")

# -------- INIT DATABASE --------
def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, username TEXT, password TEXT, role TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS slots(id INTEGER PRIMARY KEY, status TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, vehicle TEXT, entry TEXT, exit TEXT, fee INTEGER)")

    c.execute("SELECT COUNT(*) FROM slots")
    if c.fetchone()[0] == 0:
        for i in range(1, 11):
            c.execute("INSERT INTO slots(status) VALUES('Available')")

    conn.commit()
    conn.close()

init_db()

# -------- LOGIN --------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = c.fetchone()

        if user:
            session["user"] = u
            session["role"] = user[3]
            return redirect("/dashboard")
        return "Invalid Login ❌"

    return render_template("login.html")

# -------- REGISTER --------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        r = request.form.get("role")

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO users(username,password,role) VALUES(?,?,?)", (u, p, r))
        conn.commit()

        return redirect("/")

    return render_template("register.html")

# -------- DASHBOARD --------
@app.route("/dashboard")
def dashboard():
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM slots")
    slots = c.fetchall()

    return render_template("dashboard.html", slots=slots, user=session.get("user"))

# -------- PARK --------
@app.route("/park", methods=["GET", "POST"])
def park():
    if request.method == "POST":
        v = request.form.get("vehicle")

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id FROM slots WHERE status='Available' LIMIT 1")
        slot = c.fetchone()

        if slot:
            slot_id = slot[0]
            entry = str(datetime.now())

            c.execute("INSERT INTO records(vehicle, entry) VALUES(?,?)", (v, entry))
            c.execute("UPDATE slots SET status='Occupied' WHERE id=?", (slot_id,))
            conn.commit()

            return redirect("/dashboard")

        return "No Slots Available ❌"

    return render_template("park.html")

# -------- EXIT --------
@app.route("/exit", methods=["GET", "POST"])
def exit_vehicle():
    if request.method == "POST":
        v = request.form.get("vehicle")

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id, entry FROM records WHERE vehicle=? AND exit IS NULL", (v,))
        data = c.fetchone()

        if data:
            rid, entry = data
            exit_time = datetime.now()
            fee = 20

            c.execute("UPDATE records SET exit=?, fee=? WHERE id=?", (str(exit_time), fee, rid))
            c.execute("UPDATE slots SET status='Available' WHERE id=1")
            conn.commit()

            return f"Vehicle Exited ✅ Fee ₹{fee}"

        return "Vehicle Not Found ❌"

    return render_template("exit.html")

app.run(debug=True)