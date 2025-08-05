"""add reset token fields

Revision ID: add_reset_token_fields
Revises: e77cca3e01cd
Create Date: 2025-08-04 09:46:34.332

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_reset_token_fields'
down_revision: Union[str, None] = 'e77cca3e01cd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add reset_token and reset_token_expires columns to users table
    op.add_column('users', sa.Column('reset_token', sa.String(), nullable=True))
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove reset_token and reset_token_expires columns from users table
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')