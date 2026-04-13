"""Check users in database"""
from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT username, email, role::text, is_active FROM users"))
    users = result.fetchall()
    
    print(f"Total users found: {len(users)}\n")
    
    if len(users) == 0:
        print("❌ No users found in database")
    else:
        for user in users:
            print(f"Username: {user[0]}, Email: {user[1]}, Role: {user[2]}, Active: {user[3]}")
