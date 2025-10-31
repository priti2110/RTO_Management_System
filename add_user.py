from app import create_app
from app.models import Employee
from app import db

# Initialize the app
app = create_app()

def add_user():
    email = input('Enter email: ').strip()
    emp_name = input('Enter employee name: ').strip()
    password = input('Enter password: ').strip()
    role = input('Enter role (admin/employee) [employee]: ').strip() or 'employee'

    # Check if user already exists
    existing = Employee.query.filter_by(email=email).first()
    if existing:
        print('User already exists!')
        return

    user = Employee(email=email, emp_name=emp_name, role=role)
    user.set_password(password)
    db.session.add(user)
    try:
        db.session.commit()
        print(f'User {email} created successfully!')
    except Exception as e:
        db.session.rollback()
        print('Failed to create user:', e)


def list_users():
    users = Employee.query.all()
    if not users:
        print('No users found.')
        return
    print(f"{'emp_id':<30} {'emp_name':<25} {'email':<35} {'role':<10}")
    print('-' * 100)
    for u in users:
        print(f"{getattr(u, 'emp_id', ''):<30} {getattr(u, 'emp_name', ''):<25} {getattr(u, 'email', ''):<35} {getattr(u, 'role', ''):<10}")


if __name__ == '__main__':
    with app.app_context():
        while True:
            print('\nSelect an option:')
            print('1) Add user')
            print('2) List users')
            print('3) Exit')
            choice = input('Choice: ').strip()
            if choice == '1':
                add_user()
            elif choice == '2':
                list_users()
            elif choice == '3':
                break
            else:
                print('Invalid choice.')
