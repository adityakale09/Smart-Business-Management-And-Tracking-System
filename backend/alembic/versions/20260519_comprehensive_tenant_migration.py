"""Comprehensive migration: multi-tenant support, legacy cleanup, model integrity

This migration handles multiple pending changes from the current DB state:
  1. Drop legacy/unused tables with CASCADE
  2. Add missing columns to match updated models (receipts, audit_logs)
  3. Create composite indexes for query performance
  4. Create organizations table and add organization-level data isolation

Revision ID: comprehensive_tenant_migration
Revises: add_full_name_to_employee
Create Date: 2026-05-19

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "comprehensive_tenant_migration"
down_revision: Union[str, Sequence[str], None] = "add_full_name_to_employee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


LEGACY_TABLES = [
    "attendance", "categories", "customers", "expenses",
    "invoices", "permissions", "products", "role_permissions",
    "roles", "sale_items", "stock_movements", "transactions",
]


def upgrade() -> None:
    """Upgrade schema from current state to full multi-tenant architecture."""

    # =========================================================================
    # PHASE 1: Drop legacy/unused tables (with CASCADE for FK dependencies)
    # =========================================================================
    for table in LEGACY_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

    # =========================================================================
    # PHASE 2: Add missing columns to match current model definitions
    # =========================================================================

    # --- receipts: add category and notes (model has them, DB doesn't) ---
    op.add_column("receipts", sa.Column("category", sa.String(), nullable=True))
    op.add_column("receipts", sa.Column("notes", sa.Text(), nullable=True))

    # --- audit_logs: add hash chain integrity columns ---
    op.add_column("audit_logs", sa.Column("severity", sa.String(), server_default="INFO", nullable=True))
    op.add_column("audit_logs", sa.Column("old_values", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("new_values", sa.JSON(), nullable=True))
    op.add_column("audit_logs", sa.Column("correlation_id", sa.String(), nullable=True))
    # hash: must be nullable initially to populate existing rows, then set NOT NULL + unique
    op.add_column("audit_logs", sa.Column("hash", sa.String(), nullable=True))
    op.add_column("audit_logs", sa.Column("previous_hash", sa.String(), nullable=True))

    # Populate hash for existing audit log rows (generate unique hashes)
    op.execute(
        "UPDATE audit_logs SET hash = 'legacy_' || id::text || '_' || md5(random()::text) "
        "WHERE hash IS NULL"
    )
    op.execute(
        "UPDATE audit_logs SET previous_hash = "
        "  (SELECT hash FROM audit_logs AS prev WHERE prev.id = audit_logs.id - 1) "
        "WHERE previous_hash IS NULL AND id > 1"
    )
    # Set NOT NULL and UNIQUE on hash
    op.alter_column("audit_logs", "hash", nullable=False)
    op.create_unique_constraint("uq_audit_logs_hash", "audit_logs", ["hash"])

    # Set severity NOT NULL and add index
    op.alter_column("audit_logs", "severity", server_default="INFO", nullable=False)

    # --- users: role column - extend VARCHAR(8) to VARCHAR(32) for super_admin ---
    # The DB currently has VARCHAR(8) which is too small for "super_admin" (11 chars)
    # But modifying column type can be complex; let's use a safe approach
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(32) USING role::VARCHAR(32)")

    # =========================================================================
    # PHASE 3: Composite indexes for query performance
    # =========================================================================

    # Users
    op.create_index("ix_users_role_created", "users", ["role", "created_at"])
    op.create_index("ix_users_is_active_created", "users", ["is_active", "created_at"])

    # Sales
    op.create_index("ix_sales_user_created", "sales", ["user_id", "created_at"])
    op.create_index("ix_sales_status_created", "sales", ["status", "created_at"])
    op.create_index("ix_sales_product_created", "sales", ["product_id", "created_at"])
    op.create_index("ix_sales_payment_date", "sales", ["payment_method", "created_at"])

    # Inventory
    op.create_index("ix_inventory_category_status", "inventory", ["category", "status"])
    op.create_index("ix_inventory_status_quantity", "inventory", ["status", "quantity"])
    op.create_index("ix_inventory_supplier_status", "inventory", ["supplier", "status"])

    # Inventory updates
    op.create_index("ix_inv_updates_inventory_created", "inventory_updates", ["inventory_id", "created_at"])
    op.create_index("ix_inv_updates_type_created", "inventory_updates", ["update_type", "created_at"])

    # Employees
    op.create_index("ix_employees_department_status", "employees", ["department", "status"])
    op.create_index("ix_employees_status_created", "employees", ["status", "created_at"])

    # Employee attendance
    op.create_index("ix_attendance_employee_date", "employee_attendance", ["employee_id", "date"])
    op.create_index("ix_attendance_status_date", "employee_attendance", ["status", "date"])

    # Receipts
    op.create_index("ix_receipts_type_created", "receipts", ["receipt_type", "created_at"])
    op.create_index("ix_receipts_category_created", "receipts", ["category", "created_at"])
    op.create_index("ix_receipts_processed_by", "receipts", ["processed_by", "created_at"])

    # Audit logs
    op.create_index("ix_audit_logs_user_created", "audit_logs", ["user_id", "created_at"])
    op.create_index("ix_audit_logs_action_entity", "audit_logs", ["action", "entity_type"])
    op.create_index("ix_audit_logs_created_status", "audit_logs", ["created_at", "status"])
    op.create_index("ix_audit_logs_severity_created", "audit_logs", ["severity", "created_at"])
    op.create_index("ix_audit_logs_correlation_id", "audit_logs", ["correlation_id"])
    op.create_index("ix_audit_logs_previous_hash", "audit_logs", ["previous_hash"])

    # =========================================================================
    # PHASE 4: Multi-tenant organization support
    # =========================================================================

    # --- Create organizations table ---
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("organizations_pkey")),
        sa.UniqueConstraint("name", name=op.f("organizations_name_key")),
        sa.UniqueConstraint("slug", name=op.f("organizations_slug_key")),
    )
    op.create_index(op.f("ix_organizations_id"), "organizations", ["id"])
    op.create_index(op.f("ix_organizations_slug"), "organizations", ["slug"])
    op.create_index("ix_organizations_active_created", "organizations", ["is_active", "created_at"])

    # --- Insert default organization for existing data ---
    op.execute(
        "INSERT INTO organizations (name, slug, is_active, created_at, updated_at) "
        "VALUES ('Default Organization', 'default', true, NOW(), NOW())"
    )

    # --- Add organization_id to all tenant-scoped tables ---
    # Step 1: Add nullable organization_id column
    # Step 2: Populate with default org id
    # Step 3: Set NOT NULL where appropriate
    # Step 4: Create foreign key constraint

    tables = [
        {"name": "users",                "nullable": False},
        {"name": "employees",            "nullable": False},
        {"name": "employee_attendance",  "nullable": False},
        {"name": "inventory",            "nullable": False},
        {"name": "inventory_updates",    "nullable": False},
        {"name": "sales",                "nullable": False},
        {"name": "receipts",             "nullable": False},
        {"name": "receipt_items",        "nullable": False},
        {"name": "audit_logs",           "nullable": True},
    ]

    for tbl in tables:
        table = tbl["name"]
        op.add_column(table, sa.Column("organization_id", sa.Integer(), nullable=True))

        # Populate with default org
        op.execute(
            f"UPDATE {table} SET organization_id = "
            f"(SELECT id FROM organizations WHERE slug = 'default')"
        )

        if not tbl["nullable"]:
            op.alter_column(table, "organization_id", nullable=False)

        op.create_foreign_key(
            f"fk_{table}_organization",
            table, "organizations",
            ["organization_id"], ["id"],
        )

    # --- Add multi-tenant composite indexes ---
    op.create_index("ix_users_org_role", "users", ["organization_id", "role"])
    op.create_index("ix_users_org_is_active", "users", ["organization_id", "is_active"])

    op.create_index("ix_employees_org_dept_status", "employees", ["organization_id", "department", "status"])
    op.create_index("ix_employees_org_status_created", "employees", ["organization_id", "status", "created_at"])

    op.create_index("ix_attendance_org_employee_date", "employee_attendance", ["organization_id", "employee_id", "date"])
    op.create_index("ix_attendance_org_status_date", "employee_attendance", ["organization_id", "status", "date"])

    op.create_index("ix_inventory_org_category_status", "inventory", ["organization_id", "category", "status"])
    op.create_index("ix_inventory_org_status_quantity", "inventory", ["organization_id", "status", "quantity"])

    op.create_index("ix_inv_updates_org_inventory_created", "inventory_updates", ["organization_id", "inventory_id", "created_at"])
    op.create_index("ix_inv_updates_org_type_created", "inventory_updates", ["organization_id", "update_type", "created_at"])

    op.create_index("ix_sales_org_user_created", "sales", ["organization_id", "user_id", "created_at"])
    op.create_index("ix_sales_org_status_created", "sales", ["organization_id", "status", "created_at"])

    op.create_index("ix_receipts_org_type_created", "receipts", ["organization_id", "receipt_type", "created_at"])
    op.create_index("ix_receipts_org_category_created", "receipts", ["organization_id", "category", "created_at"])

    op.create_index("ix_audit_logs_org_user_created", "audit_logs", ["organization_id", "user_id", "created_at"])


def downgrade() -> None:
    """Downgrade schema - reverse the comprehensive migration."""

    # =========================================================================
    # Reverse Phase 4: Remove multi-tenant support
    # =========================================================================

    # Drop multi-tenant composite indexes
    op.drop_index("ix_audit_logs_org_user_created", table_name="audit_logs")
    op.drop_index("ix_receipts_org_category_created", table_name="receipts")
    op.drop_index("ix_receipts_org_type_created", table_name="receipts")
    op.drop_index("ix_sales_org_status_created", table_name="sales")
    op.drop_index("ix_sales_org_user_created", table_name="sales")
    op.drop_index("ix_inv_updates_org_type_created", table_name="inventory_updates")
    op.drop_index("ix_inv_updates_org_inventory_created", table_name="inventory_updates")
    op.drop_index("ix_inventory_org_status_quantity", table_name="inventory")
    op.drop_index("ix_inventory_org_category_status", table_name="inventory")
    op.drop_index("ix_attendance_org_status_date", table_name="employee_attendance")
    op.drop_index("ix_attendance_org_employee_date", table_name="employee_attendance")
    op.drop_index("ix_employees_org_status_created", table_name="employees")
    op.drop_index("ix_employees_org_dept_status", table_name="employees")
    op.drop_index("ix_users_org_is_active", table_name="users")
    op.drop_index("ix_users_org_role", table_name="users")

    # Drop foreign keys and organization_id columns
    tenant_tables = [
        "users", "employees", "employee_attendance",
        "inventory", "inventory_updates", "sales",
        "receipts", "receipt_items", "audit_logs",
    ]
    for table in tenant_tables:
        op.drop_constraint(f"fk_{table}_organization", table, type_="foreignkey")
        op.drop_column(table, "organization_id")

    # Drop organizations table
    op.drop_index("ix_organizations_active_created", table_name="organizations")
    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
    op.drop_table("organizations")

    # =========================================================================
    # Reverse Phase 3: Drop composite indexes
    # =========================================================================
    op.drop_index("ix_audit_logs_previous_hash", table_name="audit_logs")
    op.drop_index("ix_audit_logs_correlation_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_severity_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_status", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action_entity", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_created", table_name="audit_logs")

    op.drop_index("ix_receipts_processed_by", table_name="receipts")
    op.drop_index("ix_receipts_category_created", table_name="receipts")
    op.drop_index("ix_receipts_type_created", table_name="receipts")

    op.drop_index("ix_attendance_status_date", table_name="employee_attendance")
    op.drop_index("ix_attendance_employee_date", table_name="employee_attendance")

    op.drop_index("ix_employees_status_created", table_name="employees")
    op.drop_index("ix_employees_department_status", table_name="employees")

    op.drop_index("ix_inv_updates_type_created", table_name="inventory_updates")
    op.drop_index("ix_inv_updates_inventory_created", table_name="inventory_updates")

    op.drop_index("ix_inventory_supplier_status", table_name="inventory")
    op.drop_index("ix_inventory_status_quantity", table_name="inventory")
    op.drop_index("ix_inventory_category_status", table_name="inventory")

    op.drop_index("ix_sales_payment_date", table_name="sales")
    op.drop_index("ix_sales_product_created", table_name="sales")
    op.drop_index("ix_sales_status_created", table_name="sales")
    op.drop_index("ix_sales_user_created", table_name="sales")

    op.drop_index("ix_users_is_active_created", table_name="users")
    op.drop_index("ix_users_role_created", table_name="users")

    # =========================================================================
    # Reverse Phase 2: Remove added columns and restore role type
    # =========================================================================

    # Revert users.role back to VARCHAR(8)
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(8) USING role::VARCHAR(8)")

    # Remove audit_logs columns
    op.drop_constraint("uq_audit_logs_hash", "audit_logs", type_="unique")
    op.drop_column("audit_logs", "previous_hash")
    op.drop_column("audit_logs", "hash")
    op.drop_column("audit_logs", "correlation_id")
    op.drop_column("audit_logs", "new_values")
    op.drop_column("audit_logs", "old_values")
    op.drop_column("audit_logs", "severity")

    # Remove receipts columns
    op.drop_column("receipts", "notes")
    op.drop_column("receipts", "category")

    # =========================================================================
    # Reverse Phase 1: Cannot recreate dropped legacy tables with data
    # (This is a no-op - we can't restore dropped tables with their data)
    # =========================================================================
