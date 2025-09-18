"""remove telegram_chat_id from users

Revision ID: remove_telegram_chat_id
Revises: 
Create Date: 2025-09-17
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_telegram_chat_id'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    with op.batch_alter_table('users') as batch_op:
        try:
            batch_op.drop_column('telegram_chat_id')
        except Exception:
            pass

def downgrade():
    with op.batch_alter_table('users') as batch_op:
        try:
            batch_op.add_column(sa.Column('telegram_chat_id', sa.String(), nullable=True))
        except Exception:
            pass
