"""Verify Performance Indexes Were Created"""
from sqlalchemy import create_engine, text
from urllib.parse import quote_plus

# Database connection
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "ADITYA@KALE"
POSTGRES_HOST = "localhost"
POSTGRES_PORT = "5432"
POSTGRES_DB = "business_platform"

encoded_user = quote_plus(POSTGRES_USER)
encoded_password = quote_plus(POSTGRES_PASSWORD)
DATABASE_URL = f"postgresql://{encoded_user}:{encoded_password}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

engine = create_engine(DATABASE_URL)

print("="*80)
print("VERIFYING PERFORMANCE INDEXES")
print("="*80)

with engine.connect() as conn:
    # Query to get all indexes
    query = text("""
        SELECT 
            tablename,
            indexname,
            indexdef
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND indexname LIKE 'idx_%'
        ORDER BY tablename, indexname
    """)
    
    result = conn.execute(query)
    indexes = result.fetchall()
    
    if indexes:
        current_table = None
        for table, index, definition in indexes:
            if table != current_table:
                print(f"\n📋 Table: {table.upper()}")
                print("-" * 80)
                current_table = table
            print(f"   ✅ {index}")
        
        print("\n" + "="*80)
        print(f"✅ Total Performance Indexes: {len(indexes)}")
        print("="*80)
    else:
        print("\n❌ No performance indexes found")

print("\n✅ Verification complete!")
