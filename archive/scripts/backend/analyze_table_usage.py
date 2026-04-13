"""Analyze which tables are actually used by the application"""
from app.database import engine
from sqlalchemy import text, inspect

print("="*80)
print("TABLE USAGE ANALYSIS")
print("="*80)

# Tables that are actively used
active_tables = {
    'users': 'Authentication & user management',
    'inventory': 'Main inventory system (ACTIVE - used by frontend)',
    'inventory_updates': 'Inventory audit trail',
    'sales': 'Sales transactions (ACTIVE - used by frontend)',
    'employees': 'Employee records',
    'employee_attendance': 'Employee attendance tracking',
    'receipts': 'Receipt processing',
    'receipt_items': 'Receipt details',
    'audit_logs': 'Security audit logging',
    'roles': 'RBAC role definitions',
    'permissions': 'RBAC permissions',
    'role_permissions': 'RBAC role-permission mapping'
}

# Tables from old/duplicate system - NOT USED
unused_tables = {
    'products': 'DUPLICATE of inventory (old system)',
    'categories': 'Product categories (not linked to inventory)',
    'sale_items': 'ORPHANED - 293 records but disconnected from sales',
    'stock_movements': 'Not implemented',
    'transactions': 'Not implemented',
    'invoices': 'Not implemented (PDF only, not saved to DB)',
    'customers': 'Not used by frontend',
    'expenses': 'Not used by frontend',
    'attendance': 'DUPLICATE of employee_attendance'
}

print("\n✅ ACTIVE TABLES (Used by application):")
print("-" * 80)
for table, purpose in active_tables.items():
    with engine.connect() as conn:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"  {table:<30} {count:>6} records - {purpose}")
        except:
            print(f"  {table:<30}   ERROR - {purpose}")

print("\n❌ UNUSED/DUPLICATE TABLES (Can be removed):")
print("-" * 80)
for table, issue in unused_tables.items():
    with engine.connect() as conn:
        try:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.fetchone()[0]
            print(f"  {table:<30} {count:>6} records - {issue}")
        except:
            print(f"  {table:<30}   ERROR - {issue}")

print("\n" + "="*80)
print("\nRECOMMENDATION:")
print("-" * 80)
print("1. Keep all ACTIVE tables")
print("2. Remove UNUSED tables to simplify database")
print("3. This will:")
print("   - Reduce database size")
print("   - Improve performance")
print("   - Eliminate confusion")
print("   - Make codebase cleaner")
print("="*80)
