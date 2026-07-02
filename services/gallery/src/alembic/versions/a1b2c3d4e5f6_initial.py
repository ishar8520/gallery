"""initial

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-07-02 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'a1b2c3d4e5f6'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute('CREATE SCHEMA IF NOT EXISTS gallery')

    op.create_table(
        'albums',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        schema='gallery',
    )
    op.create_index('ix_gallery_albums_user_id', 'albums', ['user_id'], schema='gallery')

    op.create_table(
        'photos',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('album_id', sa.Uuid(), nullable=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(512), nullable=False),
        sa.Column('object_name', sa.String(1024), nullable=False),
        sa.Column('bucket_name', sa.String(255), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('mime_type', sa.String(128), nullable=False),
        sa.Column('exif_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['album_id'], ['gallery.albums.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        schema='gallery',
    )
    op.create_index('ix_gallery_photos_user_id', 'photos', ['user_id'], schema='gallery')
    op.create_index('ix_gallery_photos_album_id', 'photos', ['album_id'], schema='gallery')


def downgrade() -> None:
    op.drop_table('photos', schema='gallery')
    op.drop_table('albums', schema='gallery')
    op.execute('DROP SCHEMA IF EXISTS gallery')
