from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'hrms_secret_key'

# Connect to the database
def get_db():
    return sqlite3.connect('hrms.db')

# Get user from database
def get_user(userid, password):
    con = get_db()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE userid = ? AND password = ?", (userid, password))
    user = cur.fetchone()
    con.close()
    return user

# Create tables (run once)
def create_tables():
    con = get_db()
    cur = con.cursor()

    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userid TEXT UNIQUE,
        password TEXT,
        firstname TEXT,
        middlename TEXT,
        lastname TEXT,
        fathername TEXT,
        dob TEXT,
        address TEXT,
        aadhar_no TEXT,
        pan_no TEXT,
        bank_account TEXT,
        ifsc TEXT,
        micr_core TEXT,
        joining_date TEXT,
        status TEXT DEFAULT 'Pending'
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        userid TEXT,
        date TEXT,
        time TEXT
    )''')

    con.commit()
    con.close()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Register new user
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = (
            request.form['userid'], request.form['password'],
            request.form['firstname'], request.form['middlename'],
            request.form['lastname'], request.form['fathername'],
            request.form['dob'], request.form['address'],
            request.form['aadhar_no'], request.form['pan_no'],
            request.form['bank_account'], request.form['ifsc'],
            request.form['micr_core'], request.form['joining_date'],
            'Pending'
        )
        con = get_db()
        cur = con.cursor()
        cur.execute('''INSERT INTO users (
            userid, password, firstname, middlename, lastname, fathername,
            dob, address, aadhar_no, pan_no, bank_account,
            ifsc, micr_core, joining_date, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data)
        con.commit()
        con.close()
        return redirect(f'/status/{request.form["userid"]}')
    return render_template('register.html')

# Status by user ID
@app.route('/status/<userid>')
def status(userid):
    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT status FROM users WHERE userid = ?", (userid,))
    result = cur.fetchone()
    con.close()

    if result:
        return render_template('status.html', userid=userid, status=result[0])
    else:
        return "User not found", 404

# Status lookup page
@app.route('/status', methods=['GET', 'POST'])
def status_lookup():
    if request.method == 'POST':
        userid = request.form['userid']
        return redirect(f'/status/{userid}')
    return render_template('status_lookup.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        userid = request.form['userid']
        password = request.form['password']
        user = get_user(userid, password)

        if user:
            if user['status'] == 'Rejected':
                return render_template('status_message.html', message="❌ Your application was rejected. You cannot login.", color="red")
            elif user['status'] == 'Pending':
                return render_template('status_message.html', message="⏳ Your application is still pending. Please wait for HR approval.", color="orange")
            elif user['status'] == 'Approved':
                session['user'] = user['userid']
                return redirect('/dashboard')
        else:
            flash("Invalid User ID or Password")
            return redirect('/login')

    return render_template('login.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')

    con = get_db()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE userid=?", (session['user'],))
    user = cur.fetchone()
    con.close()

    if not user:
        return "User not found", 404

    return render_template('dashboard.html', user=user)

# Mark Attendance
@app.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if 'user' not in session:
        return redirect('/login')

    punch_time = None
    punch_date = None

    if request.method == 'POST':
        now = datetime.now()
        punch_date = now.strftime("%Y-%m-%d")
        punch_time = now.strftime("%I:%M:%S %p")

        con = get_db()
        cur = con.cursor()
        cur.execute("INSERT INTO attendance (userid, date, time) VALUES (?, ?, ?)",
                    (session['user'], punch_date, punch_time))
        con.commit()
        con.close()

    return render_template('attendance.html', punch_time=punch_time, punch_date=punch_date)

# View Attendance
@app.route('/view_attendance')
def view_attendance():
    if 'user' not in session:
        return redirect('/login')

    con = get_db()
    cur = con.cursor()
    cur.execute("SELECT date, time FROM attendance WHERE userid = ?", (session['user'],))
    records = cur.fetchall()
    con.close()

    return render_template('view_attendance.html', records=records)

# View employee
@app.route('/employee/<userid>')
def view_employee(userid):
    con = get_db()
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE userid=?", (userid,))
    employee = cur.fetchone()
    con.close()

    if employee:
        return render_template('view_employee.html', employee=employee)
    else:
        return "Employee not found", 404

# Edit employee
@app.route('/employee/<userid>/edit', methods=['GET', 'POST'])
def edit_employee(userid):
    con = get_db()
    cur = con.cursor()

    if request.method == 'POST':
        data = (
            request.form.get('password'),
            request.form.get('firstname'),
            request.form.get('middlename'),
            request.form.get('lastname'),
            request.form.get('fathername'),
            request.form.get('dob'),
            request.form.get('address'),
            request.form.get('aadhar_no'),
            request.form.get('pan_no'),
            request.form.get('bank_account'),
            request.form.get('ifsc'),
            request.form.get('micr_core'),
            request.form.get('joining_date'),
            userid
        )

        cur.execute("""
            UPDATE users SET 
                password=?, firstname=?, middlename=?, lastname=?, fathername=?, dob=?, address=?,
                aadhar_no=?, pan_no=?, bank_account=?, ifsc=?, micr_core=?, joining_date=?
            WHERE userid=?
        """, data)
        con.commit()
        con.close()
        return redirect(f'/employee/{userid}')

    cur.execute("SELECT * FROM users WHERE userid=?", (userid,))
    employee = cur.fetchone()
    con.close()

    if employee:
        return render_template('edit_employee.html', employee=employee)
    else:
        return "Employee not found", 404

# HR Panel
@app.route('/hr_panel', methods=['GET', 'POST'])
def hr_panel():
    con = get_db()
    cur = con.cursor()

    if request.method == 'POST':
        action = request.form.get('action')
        userid = request.form.get('userid')
        new_status = 'Approved' if action == 'approve' else 'Rejected'

        cur.execute("UPDATE users SET status=? WHERE userid=?", (new_status, userid))
        con.commit()

    cur.execute("SELECT userid, firstname, middlename, lastname, joining_date, status FROM users")
    users = cur.fetchall()
    con.close()

    return render_template('hr_panel.html', users=users)

# Logout
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# Create tables on startup
create_tables()

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)
