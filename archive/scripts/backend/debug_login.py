"""Debug login process"""
from app.database import SessionLocal
from app.models.user import User
from app.core.security import verify_password

db = SessionLocal()

username = "admin"
password = "admin123"

# Step 1: Query user
user = db.query(User).filter(User.username == username).first()
print(f"[1] User query result: {user}")
if user:
    print(f"    ID: {user.id}")
    print(f"    Username: {user.username}")
    print(f"    Email: {user.email}")
    print(f"    is_active type: {type(user.is_active)}")
    print(f"    is_active value: {user.is_active}")
    print(f"    is_active bool: {bool(user.is_active)}")

# Step 2: Check if user exists
print(f"\n[2] User exists? {user is not None}")

# Step 3: Verify password
if user:
    pwd_match = verify_password(password, user.hashed_password)
    print(f"\n[3] Password match: {pwd_match}")
    print(f"    Provided password: {password}")
    print(f"    Hashed password: {user.hashed_password[:50]}...")

# Step 4: Check the login condition
if user and verify_password(password, user.hashed_password):
    print(f"\n[4] Credentials valid: TRUE")
    
    # Step 5: Check is_active
    if not user.is_active:
        print(f"[5] ERROR: User inactive")
    else:
        print(f"[5] SUCCESS: User is active")
else:
    print(f"\n[4] Credentials valid: FALSE")

db.close()
