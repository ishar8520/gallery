"""Init values

Revision ID: 462161efa2d8
Revises: 72d19721c105
Create Date: 2025-06-27 11:54:45.840388

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from src.models.enums import Roles

# revision identifiers, used by Alembic.
revision: str = '462161efa2d8'
down_revision: Union[str, None] = '72d19721c105'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    roles_table = sa.table(
        'roles',
        schema='auth'
    )
    op.bulk_insert(
        roles_table,
        [
            {'role': Roles.USER.value,},
            {'role': Roles.ADMIN.value,}
        ]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute('TRUNCATE auth.roles')
