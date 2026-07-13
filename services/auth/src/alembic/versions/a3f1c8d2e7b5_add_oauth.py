"""Add OAuth accounts table and make password nullable

Revision ID: a3f1c8d2e7b5
Revises: 192db30b56b4
Create Date: 2026-07-13 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'a3f1c8d2e7b5'
down_revision: str | None = '192db30b56b4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column('users', 'password', nullable=True, schema='auth')
    op.create_table(
        'oauth_accounts',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.UUID(as_uuid=True),
                  sa.ForeignKey('auth.users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_user_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('provider', 'provider_user_id',
                            name='uq_oauth_accounts_provider_provider_user_id'),
        schema='auth',
    )


def downgrade() -> None:
    op.drop_table('oauth_accounts', schema='auth')
    op.alter_column('users', 'password', nullable=False, schema='auth')
