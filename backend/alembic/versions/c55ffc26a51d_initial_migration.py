"""Initial migration

Revision ID: c55ffc26a51d
Revises: 34b37adb9fa4
Create Date: 2026-04-14 22:34:53.237564

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c55ffc26a51d"
down_revision: Union[str, Sequence[str], None] = "34b37adb9fa4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # No-op safety revision. Keep schema unchanged.
    pass


def downgrade() -> None:
    """Downgrade schema."""
    # No-op safety revision.
    pass
