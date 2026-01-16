"""
Database connections and initialization
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from urllib.parse import quote_plus

from app.core.config import settings

# PostgreSQL (SQLAlchemy) - URL-encode username and password to handle special characters
encoded_user = quote_plus(str(settings.POSTGRES_USER))
encoded_password = quote_plus(str(settings.POSTGRES_PASSWORD))
DATABASE_URL = f"postgresql://{encoded_user}:{encoded_password}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"

# Debug: Print connection string (without password) if DEBUG mode
if settings.DEBUG:
    print(f"[*] Connecting to PostgreSQL: postgresql://{settings.POSTGRES_USER}:***@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MongoDB
mongodb_client = MongoClient(settings.MONGODB_URL)
mongodb_db = mongodb_client[settings.MONGODB_DB]


def get_db():
    """Get PostgreSQL database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mongodb():
    """Get MongoDB database"""
    return mongodb_db


def test_postgres_connection():
    """Test PostgreSQL connection"""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return True, "PostgreSQL connection successful"
    except Exception as e:
        return False, f"PostgreSQL connection failed: {str(e)}"


def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        mongodb_client.admin.command('ping')
        return True, "MongoDB connection successful"
    except Exception as e:
        return False, f"MongoDB connection failed: {str(e)}"


async def init_db():
    """Initialize databases"""
    
    print("\n" + "="*60)
    print("DATABASE INITIALIZATION")
    print("="*60)
    
    # Test PostgreSQL connection first
    print("\n[1/3] Testing PostgreSQL connection...")
    postgres_ok, postgres_msg = test_postgres_connection()
    print(f"  {postgres_msg}")
    
    if not postgres_ok:
        print(f"\n[!] PostgreSQL Connection Details:")
        print(f"    Host: {settings.POSTGRES_HOST}")
        print(f"    Port: {settings.POSTGRES_PORT}")
        print(f"    Database: {settings.POSTGRES_DB}")
        print(f"    User: {settings.POSTGRES_USER}")
        print(f"\n[!] Troubleshooting:")
        print(f"    1. Ensure PostgreSQL service is running")
        print(f"    2. Verify database '{settings.POSTGRES_DB}' exists")
        print(f"    3. Check credentials in .env file")
        print(f"    4. Test connection: psql -h {settings.POSTGRES_HOST} -U {settings.POSTGRES_USER} -d {settings.POSTGRES_DB}")
        raise ConnectionError(f"PostgreSQL connection failed: {postgres_msg}")
    
    # Test MongoDB connection
    print("\n[2/3] Testing MongoDB connection...")
    mongodb_ok, mongodb_msg = test_mongodb_connection()
    print(f"  {mongodb_msg}")
    
    if not mongodb_ok:
        print(f"\n[!] MongoDB Connection Details:")
        print(f"    URL: {settings.MONGODB_URL}")
        print(f"    Database: {settings.MONGODB_DB}")
        print(f"\n[!] Troubleshooting:")
        print(f"    1. Ensure MongoDB service is running")
        print(f"    2. Check MongoDB URL in .env file")
        print(f"    3. Test connection: mongosh {settings.MONGODB_URL}")
        # Don't raise error for MongoDB, as it might not be critical for all features
        print(f"    [WARNING] Continuing without MongoDB...")
    
    # Create tables in PostgreSQL
    print("\n[3/3] Creating database tables...")
    try:
        from app.models import user, sales, inventory, employee, receipt
        Base.metadata.create_all(bind=engine)
        print("  Tables created successfully")
    except Exception as e:
        print(f"  [!] Error creating tables: {e}")
        raise
    
    print("\n" + "="*60)
    print("[+] Database initialization completed successfully!")
    print("="*60 + "\n")



