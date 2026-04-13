from app.database import SessionLocal, DATABASE_URL
from app.core.config import settings

print("="*60)
print("APP DATABASE CONFIGURATION:")
print("="*60)
print(f"POSTGRES_HOST: {settings.POSTGRES_HOST}")
print(f"POSTGRES_PORT: {settings.POSTGRES_PORT}")
print(f"POSTGRES_DB: {settings.POSTGRES_DB}")
print(f"DATABASE_URL: {DATABASE_URL.replace(settings.POSTGRES_PASSWORD, '***')}")

print("\n" + "="*60)
print("CHECKING DATABASE CONTENTS:")
print("="*60)

db = SessionLocal()

# List all users
from app.models.user import User
users = db.query(User).all()
print(f"\nTotal users in connected database: {len(users)}")
for u in users:
    print(f"  - {u.username} (id={u.id}, is_active={u.is_active})")

db.close()
