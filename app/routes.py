from flask import Blueprint, render_template, redirect, url_for, request, flash, session, send_file, abort
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
    if (getattr(current_user, 'role', '') or '').strip().lower() == 'manager':
        return redirect(url_for('main.manager_dashboard'))
    today = date.today()
    # pagination for attendance
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    attendance_query = Attendance.query.filter_by(emp_id=current_user.emp_id).order_by(Attendance.date.desc())
    attendance_pagination = attendance_query.paginate(page=page, per_page=per_page, error_out=False)
    attendance = attendance_pagination.items
    return render_template('dashboard.html', attendance=attendance, today=today, attendance_pagination=attendance_pagination)

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
            status = request.form.get(f'status_{day}')
            hours = request.form.get(f'hours_{day}')
            att = attendance_map.get(day)
            att_date = date(year, month, day)
            # If attendance record exists and is not yet submitted, update it
            if att and not att.submitted:
                if status:
                    att.status = status
                if hours:
                    try:
                        att.hours = float(hours)
                    except ValueError:
                        att.hours = None
                att.submitted = True
            # If no record exists, create one using provided inputs
            elif not att and (status or hours):
                new_att = Attendance(
                    emp_id=current_user.emp_id,
                    date=att_date,
                    status=status if status else None,
                    hours=float(hours) if hours else None,
                    submitted=True
                )
                db.session.add(new_att)
        db.session.commit()
        flash('Timesheet submitted!')
        # reload records and map after commit
        records = Attendance.query.filter_by(emp_id=current_user.emp_id).filter(db.extract('month', Attendance.date)==month, db.extract('year', Attendance.date)==year).all()
        attendance_map = {a.date.day: a for a in records}
    return render_template('timesheet.html', days=days_in_month, month=month, year=year, attendance=attendance_map)

@main.route('/manager')
@login_required
def manager_dashboard():
    if (getattr(current_user, 'role', '') or '').strip().lower() != 'manager':
        return redirect(url_for('main.dashboard'))
    # allow manager to filter by month/year
    today = date.today()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)
    days_in_month = (date(year, month % 12 + 1, 1) - date(year, month, 1)).days

    # pagination for team list
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    team_query = Employee.query.filter_by(manager_id=current_user.emp_id).order_by(Employee.emp_name)
    team_pagination = team_query.paginate(page=page, per_page=per_page, error_out=False)
    team = team_pagination.items

    team_timesheets = []
    for emp in team:
        records = Attendance.query.filter_by(emp_id=emp.emp_id).filter(db.extract('month', Attendance.date)==month, db.extract('year', Attendance.date)==year).all()
        attendance_map = {a.date.day: a for a in records}
        team_timesheets.append({'employee': emp, 'attendance': attendance_map})

    return render_template('manager_dashboard.html', team_timesheets=team_timesheets, month=month, year=year, days=days_in_month, team_pagination=team_pagination)

@main.route('/manager/download')
@login_required
def download_report():
    if (getattr(current_user, 'role', '') or '').strip().lower() != 'manager':
        return redirect(url_for('main.dashboard'))
    # support optional month/year filters via query params and per-employee download
    month = request.args.get('month', type=int)
    year = request.args.get('year', type=int)
    # parse emp_id as integer so comparisons against DB ints work
    emp_id = request.args.get('emp_id', type=int)

    # get manager's team
    team = Employee.query.filter_by(manager_id=current_user.emp_id).all()
    emp_ids = [e.emp_id for e in team]

    # If emp_id is provided, ensure it's one of the manager's team
    if emp_id:
        if emp_id not in emp_ids:
            # forbidden: trying to download someone not on your team
            abort(403)
        emp_ids = [emp_id]

    query = Attendance.query.filter(Attendance.emp_id.in_(emp_ids))
    if month and year:
        query = query.filter(db.extract('month', Attendance.date)==month, db.extract('year', Attendance.date)==year)
    records = query.all()
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
    filename = 'team_timesheet'
    if emp_id:
        filename = f'emp_{emp_id}_timesheet'
    if month and year:
        filename += f'_{year}_{month:02d}'
    filename += '.xlsx'
    return send_file(output, download_name=filename, as_attachment=True)
