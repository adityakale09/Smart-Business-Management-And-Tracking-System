from app.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

try:
    db = SessionLocal()
    # Get admin user
    admin = db.query(User).filter(User.username == 'admin').first()
    
    if admin:
        print(f"BEFORE: is_active={admin.is_active}, id={admin.id}")
        # Force update
        admin.is_active = True
        admin.hashed_password = get_password_hash("admin123")
        db.commit()
        db.refresh(admin)
        print(f"AFTER: is_active={admin.is_active}")
        print("[SUCCESS] Admin updated and committed")
    else:
        print("[ERROR] Admin user not found- creating new one")
        new_admin = User(
            username="admin",
            email="admin@business.local",
            hashed_password=get_password_hash("admin123"),
            is_active=True
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        print(f"[CREATED] New admin with id={new_admin.id}, is_active={new_admin.is_active}")
    
    db.close()
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
