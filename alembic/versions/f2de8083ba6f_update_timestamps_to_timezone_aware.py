"""update_timestamps_to_timezone_aware

Revision ID: f2de8083ba6f
Revises: d1c68a88bac0
Create Date: 2025-08-09 18:26:52.552583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2de8083ba6f'
down_revision: Union[str, Sequence[str], None] = 'd1c68a88bac0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
