from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()

print("="*60)
print("ADMIN USER STATE IN DATABASE:")
print("="*60)
if admin:
    print(f"ID: {admin.id}")
    print(f"Username: {admin.username}")
    print(f"Email: {admin.email}")
    print(f"is_active (raw): {admin.is_active}")
    print(f"is_active (type): {type(admin.is_active)}")
    print(f"is_active == True: {admin.is_active == True}")
    print(f"is_active is True: {admin.is_active is True}")
    print(f"bool(is_active): {bool(admin.is_active)}")
    print(f"role: {admin.role}")
else:
    print("ERROR: Admin user not found!")

db.close()
