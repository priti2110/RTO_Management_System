from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_file
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, Employee, Attendance
from werkzeug.security import check_password_hash
from datetime import date, datetime
import pandas as pd
import io

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Employee.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'manager':
        return redirect(url_for('main.manager_dashboard'))
    today = date.today()
    attendance = Attendance.query.filter_by(emp_id=current_user.emp_id).all()
    return render_template('dashboard.html', attendance=attendance, today=today)

@main.route('/timesheet', methods=['GET', 'POST'])
@login_required
def timesheet():
    today = date.today()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)
    days_in_month = (date(year, month % 12 + 1, 1) - date(year, month, 1)).days
    records = Attendance.query.filter_by(emp_id=current_user.emp_id).filter(db.extract('month', Attendance.date)==month, db.extract('year', Attendance.date)==year).all()
    attendance_map = {a.date.day: a for a in records}
    if request.method == 'POST':
        for day in range(1, days_in_month+1):
            hours = request.form.get(f'hours_{day}')
            att = attendance_map.get(day)
            if att and not att.submitted:
                att.hours = float(hours) if hours else None
                att.submitted = True
        db.session.commit()
        flash('Timesheet submitted!')
    return render_template('timesheet.html', days=days_in_month, month=month, year=year, attendance=attendance_map)

@main.route('/manager')
@login_required
def manager_dashboard():
    if current_user.role != 'manager':
        return redirect(url_for('main.dashboard'))
    team = Employee.query.filter_by(manager_id=current_user.emp_id).all()
    return render_template('manager_dashboard.html', team=team)

@main.route('/manager/download')
@login_required
def download_report():
    if current_user.role != 'manager':
        return redirect(url_for('main.dashboard'))
    team = Employee.query.filter_by(manager_id=current_user.emp_id).all()
    emp_ids = [e.emp_id for e in team]
    records = Attendance.query.filter(Attendance.emp_id.in_(emp_ids)).all()
    data = [
        {
            'Employee': r.emp.emp_name,
            'Date': r.date,
            'Status': 'WFO' if r.status == 'Y' else 'WFH' if r.status == 'N' else 'Leave',
            'Hours': r.hours
        } for r in records
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return send_file(output, download_name='team_timesheet.xlsx', as_attachment=True)
