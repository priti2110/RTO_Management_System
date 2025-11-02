from app import create_app, db
from app.models import Employee

app = create_app()

"""Small helper to create a manager user for testing.
Usage: python create_user_ravi.py
It will prompt for email, name and password (defaults provided).
"""

DEFAULT_EMAIL = 'manager@example.com'
DEFAULT_NAME = 'Manager User'

if __name__ == '__main__':
    with app.app_context():
        email = input(f'Email [{DEFAULT_EMAIL}]: ').strip() or DEFAULT_EMAIL
        emp_name = input(f'Name [{DEFAULT_NAME}]: ').strip() or DEFAULT_NAME
        password = input('Password [changeme]: ').strip() or 'changeme'

        existing = Employee.query.filter_by(email=email).first()
        if existing:
            print('User already exists: ', existing.emp_id, existing.email, existing.role)
        else:
            # generate emp_id similarly to add_user to avoid NULL PK errors
            try:
                existing_ids = [e.emp_id for e in Employee.query.with_entities(Employee.emp_id).all()]
                numeric_ids = [int(i) for i in existing_ids if i is not None and str(i).strip().isdigit()]
                if numeric_ids:
                    new_emp_id = max(numeric_ids) + 1
                else:
                    new_emp_id = 1001
            except Exception:
                new_emp_id = 1001

            user = Employee(emp_id=new_emp_id, email=email, emp_name=emp_name, role='manager')
            user.set_password(password)
            db.session.add(user)
            try:
                db.session.commit()
                print(f'Manager user {email} created successfully!')
            except Exception as e:
                db.session.rollback()
                print('Failed to create user:', e)
