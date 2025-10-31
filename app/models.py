from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Employee(UserMixin, db.Model):
    __tablename__ = 'employees'
    emp_id = db.Column(db.String, primary_key=True)
    emp_name = db.Column(db.String, nullable=False)
    manager_id = db.Column(db.String, db.ForeignKey('employees.emp_id'))
    email = db.Column(db.String, unique=True, nullable=False)
    password_hash = db.Column(db.String, nullable=False)
    role = db.Column(db.String, default='employee')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Attendance(db.Model):
    __tablename__ = 'employee_attendance'
    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String, db.ForeignKey('employees.emp_id'))
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(1), nullable=False)  # Y, N, L
    hours = db.Column(db.Float)
    submitted = db.Column(db.Boolean, default=False)
    emp = db.relationship('Employee', backref='attendance')
