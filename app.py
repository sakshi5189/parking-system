from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret123"

# ---------- AUTO CREATE DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        password TEXT,
        role TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_slot (
        slot_id INTEGER PRIMARY KEY,
        status TEXT
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO parking_slot VALUES
    (1,'Available'),
    (2,'Available'),
    (3,'Available')
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicle (
        vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_number TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS parking_record (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        vehicle_id INTEGER,
        slot_id INTEGER,
        entry_time TEXT,
        exit_time TEXT,
        fee INTEGER
    )
    """)

    conn.commit()
    conn.close()

# Run once when app starts
init_db()

# ---------- DATABASE CONNECTION ----------
def get_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p))
        user = cursor.fetchone()
        conn.close()

        if user:
            session["user"] = u
            session["role"] = user["role"]
            return redirect("/dashboard")
        else:
            return "Invalid Login"

    return render_template("login.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        role = request.form.get("role")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (u, p, role))
        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("register.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

# ---------- VIEW SLOTS ----------
@app.route("/slots")
def slots():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM parking_slot")
    data = cursor.fetchall()
    conn.close()

    return render_template("dashboard.html", slots=data)

# ---------- PARK VEHICLE ----------
@app.route("/park", methods=["GET", "POST"])
def park():
    if request.method == "POST":
        vnum = request.form.get("vehicle")
        slot_id = request.form.get("slot")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("INSERT INTO vehicle (vehicle_number) VALUES (?)", (vnum,))
        vehicle_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO parking_record (vehicle_id, slot_id, entry_time)
            VALUES (?, ?, ?)
        """, (vehicle_id, slot_id, datetime.now()))

        cursor.execute("UPDATE parking_slot SET status='Occupied' WHERE slot_id=?", (slot_id,))

        conn.commit()
        conn.close()

        return "Vehicle Parked Successfully"

    return render_template("park.html")

# ---------- EXIT VEHICLE ----------
@app.route("/exit", methods=["GET", "POST"])
def exit_vehicle():
    if request.method == "POST":
        vnum = request.form.get("vehicle")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT pr.record_id, pr.entry_time, pr.slot_id
            FROM parking_record pr
            JOIN vehicle v ON pr.vehicle_id = v.vehicle_id
            WHERE v.vehicle_number=? AND pr.exit_time IS NULL
        """, (vnum,))

        data = cursor.fetchone()

        if data:
            record_id = data["record_id"]
            entry_time = datetime.fromisoformat(data["entry_time"])
            slot_id = data["slot_id"]

            exit_time = datetime.now()
            hours = (exit_time - entry_time).seconds // 3600 + 1
            fee = hours * 20

            cursor.execute("""
                UPDATE parking_record
                SET exit_time=?, fee=?
                WHERE record_id=?
            """, (exit_time, fee, record_id))

            cursor.execute("UPDATE parking_slot SET status='Available' WHERE slot_id=?", (slot_id,))

            conn.commit()
            conn.close()

            return f"Vehicle Exited. Fee: ₹{fee}"

        else:
            conn.close()
            return "No active record found!"

    return render_template("exit.html")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)