"""add state_json to chat_sessions

Revision ID: a1b2c3d4e5f6
Revises: dd53b1a6c0c6
Create Date: 2026-04-05 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = 'dd53b1a6c0c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add state_json column for persisting working-memory state."""
    op.add_column('chat_sessions', sa.Column('state_json', sa.Text(), nullable=True))


def downgrade() -> None:
    """Remove state_json column."""
    op.drop_column('chat_sessions', 'state_json')

