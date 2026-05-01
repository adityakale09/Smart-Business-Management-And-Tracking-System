"""
Add full_name field to Employee model
Revision ID: add_full_name_to_employee
Revises: c8aa5b70ea12
Create Date: 2026-04-24
"""
revision = 'add_full_name_to_employee'
down_revision = 'c8aa5b70ea12'
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('employees', sa.Column('full_name', sa.String(), nullable=True))

def downgrade():
    op.drop_column('employees', 'full_name')
