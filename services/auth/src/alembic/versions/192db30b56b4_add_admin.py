"""Add admin

Revision ID: 192db30b56b4
Revises: 462161efa2d8
Create Date: 2025-07-04 12:08:41.508796

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from hashlib import sha256

from src.core.superuser import admin


# revision identifiers, used by Alembic.
revision: str = '192db30b56b4'
down_revision: Union[str, None] = '462161efa2d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    password = sha256(admin.password.encode('utf-8')).hexdigest()
    stmt = (f"""
        INSERT INTO auth.users (id, username, password, email, created_at, updated_at)
        VALUES (gen_random_uuid(), '{admin.username}', '{password}', '{admin.email}', now(), now())""")
    op.execute(stmt)
    stmt = (f"""
            SELECT """)

def downgrade() -> None:
    """Downgrade schema."""
    op.execute(f"""
               DELETE FROM auth.users WHERE username='admin'""")
