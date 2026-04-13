"""Display all database tables and their relationships"""
from app.database import engine
from sqlalchemy import inspect, text

print("="*80)
print("DATABASE STRUCTURE - SMART BUSINESS MANAGEMENT SYSTEM")
print("="*80)

inspector = inspect(engine)
tables = inspector.get_table_names()

print(f"\nTotal Tables: {len(tables)}\n")

for table_name in sorted(tables):
    print(f"\n📋 Table: {table_name.upper()}")
    print("-" * 80)
    
    columns = inspector.get_columns(table_name)
    print(f"   Columns ({len(columns)}):")
    for col in columns:
        col_type = str(col['type'])
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        pk = "PRIMARY KEY" if col.get('primary_key') else ""
        print(f"      - {col['name']:<25} {col_type:<20} {nullable:<10} {pk}")
    
    # Foreign keys
    fks = inspector.get_foreign_keys(table_name)
    if fks:
        print(f"\n   Foreign Keys:")
        for fk in fks:
            print(f"      - {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

print("\n" + "="*80)

# Count records in each table
print("\nRECORD COUNTS:")
print("-" * 80)
with engine.connect() as conn:
    for table in sorted(tables):
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"   {table:<30} {count:>10} records")
        except Exception as e:
            print(f"   {table:<30} Error: {e}")

print("\n" + "="*80)
