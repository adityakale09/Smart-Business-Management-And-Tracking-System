#!/usr/bin/env python
"""Reset admin user in local business_platform database"""
import sys
import time
sys.path.insert(0, 'backend')

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.core.security import get_password_hash

# Wait for backend to initialize
time.sleep(2)

try:
    db = SessionLocal()
    
    # Check if admin user exists
    admin = db.query(User).filter(User.username == "admin").first()
    
    if admin:
        print(f"[FOUND] Admin user exists with ID {admin.id}")
        print(f"  - Email: {admin.email}")
        print(f"  - Active: {admin.is_active}")
    else:
        print("[NOT FOUND] Admin user does not exist. Creating...")
        admin = User(
            username="admin",
            email="admin@business.local",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        print(f"[CREATED] Admin user with ID {admin.id}")
    
    # Always update password to admin123
    print(f"[UPDATE] Setting password to: admin123")
    admin.hashed_password = get_password_hash("admin123")
    admin.is_active = True
    db.commit()
    
    print("\n" + "="*50)
    print("✓ LOCAL ADMIN CREDENTIALS SET:")
    print("="*50)
    print(f"  Username: admin")
    print(f"  Password: admin123")
    print("  Database: business_platform (local)")
    print("="*50)
    
    db.close()
    
except Exception as e:
    print(f"[ERROR] {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
