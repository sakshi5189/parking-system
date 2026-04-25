from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# 🔴 Replace with your DB details (IMPORTANT)
conn = mysql.connector.connect(
   MYSQL_DATABASE
*******



MYSQL_PUBLIC_URL
*******




MYSQL_ROOT_PASSWORD
*******



MYSQL_URL
*******



MYSQLDATABASE
*******



MYSQLHOST
*******



MYSQLPASSWORD
*******



MYSQLPORT
*******



MYSQLUSER
*******





)

cursor = conn.cursor()

@app.route("/")
def home():
    cursor.execute("SELECT * FROM parking_slot")
    slots = cursor.fetchall()
    return render_template("index.html", slots=slots)

@app.route("/park", methods=["GET", "POST"])
def park():
    if request.method == "POST":
        vnum = request.form["vnum"]
        owner = request.form["owner"]

        cursor.execute(
            "INSERT INTO vehicle(vehicle_number, owner_name) VALUES (%s,%s)",
            (vnum, owner)
        )
        conn.commit()

        cursor.execute("SELECT LAST_INSERT_ID()")
        vid = cursor.fetchone()[0]

        cursor.execute("SELECT slot_id FROM parking_slot WHERE status='Available' LIMIT 1")
        slot = cursor.fetchone()

        if slot:
            slot_id = slot[0]
            entry = datetime.now()

            cursor.execute(
                "INSERT INTO parking_record(vehicle_id, slot_id, entry_time) VALUES (%s,%s,%s)",
                (vid, slot_id, entry)
            )

            cursor.execute(
                "UPDATE parking_slot SET status='Occupied' WHERE slot_id=%s",
                (slot_id,)
            )

            conn.commit()

        return redirect("/")

    return render_template("park.html")

@app.route("/exit", methods=["GET", "POST"])
def exit_vehicle():
    if request.method == "POST":
        record_id = request.form["record_id"]

        cursor.execute(
            "SELECT entry_time, slot_id FROM parking_record WHERE record_id=%s AND exit_time IS NULL",
            (record_id,)
        )
        data = cursor.fetchone()

        if data:
            entry_time, slot_id = data
            exit_time = datetime.now()

            hours = int((exit_time - entry_time).total_seconds() // 3600) + 1
            fee = hours * 20

            cursor.execute(
                "UPDATE parking_record SET exit_time=%s, fee=%s WHERE record_id=%s",
                (exit_time, fee, record_id)
            )

            cursor.execute(
                "UPDATE parking_slot SET status='Available' WHERE slot_id=%s",
                (slot_id,)
            )

            conn.commit()

        return redirect("/")

    return render_template("exit.html")

if __name__ == "__main__":
    app.run(debug=True)