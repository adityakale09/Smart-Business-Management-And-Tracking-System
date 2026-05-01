"""Initial migration baseline

Revision ID: 34b37adb9fa4
Revises:
Create Date: 2026-04-14 22:30:19.229073

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "34b37adb9fa4"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Baseline migration: keep existing database schema unchanged.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No-op because baseline migration should not alter existing schema.
    pass
