"""unique username

Revision ID: 5b1e0c7a9d3f
Revises: 14dbf9f7c611
Create Date: 2026-10-07 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5b1e0c7a9d3f'
down_revision: Union[str, None] = '14dbf9f7c611'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint('users_username_key', 'users', ['username'])


def downgrade() -> None:
    op.drop_constraint('users_username_key', 'users', type_='unique')
