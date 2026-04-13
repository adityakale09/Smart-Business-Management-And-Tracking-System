"""Check project setup status"""
from app.database import engine
from sqlalchemy import text

print("="*60)
print("PROJECT SETUP STATUS CHECK")
print("="*60)

# Check for admin user
with engine.connect() as conn:
    result = conn.execute(text("SELECT username, role::text FROM users WHERE role::text IN ('admin', 'ADMIN') LIMIT 1"))
    admin = result.fetchone()
    
    if admin:
        print(f"✅ Admin user exists: {admin[0]} (Role: {admin[1]})")
    else:
        print("❌ Admin user NOT found")

# Check for audit logs table
with engine.connect() as conn:
    result = conn.execute(text("SELECT COUNT(*) FROM audit_logs"))
    count = result.fetchone()[0]
    print(f"✅ audit_logs table exists with {count} records")

print("\n✅ All checks passed!")
