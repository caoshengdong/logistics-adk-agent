"""add message_id to artifacts

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add message_id FK to artifacts so artifacts persist with messages."""
    op.add_column(
        'artifacts',
        sa.Column('message_id', sa.String(32), sa.ForeignKey('chat_messages.id', ondelete='SET NULL'), nullable=True),
    )
    op.create_index('ix_artifacts_message_id', 'artifacts', ['message_id'])


def downgrade() -> None:
    """Remove message_id from artifacts."""
    op.drop_index('ix_artifacts_message_id', table_name='artifacts')
    op.drop_column('artifacts', 'message_id')

