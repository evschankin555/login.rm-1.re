"""Initial migration

Revision ID: 298b9269ae97
Revises: b0c7bda30b2e
Create Date: 2024-06-21 20:14:55.998951

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '298b9269ae97'
down_revision: Union[str, None] = 'b0c7bda30b2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('code', sa.String(), nullable=True))
    op.add_column('users', sa.Column('guide', sa.String(), nullable=True))
    op.drop_index('ix_users_name', table_name='users')
    op.create_index(op.f('ix_users_code'), 'users', ['code'], unique=True)
    op.create_index(op.f('ix_users_guide'), 'users', ['guide'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_guide'), table_name='users')
    op.drop_index(op.f('ix_users_code'), table_name='users')
    op.create_index('ix_users_name', 'users', ['name'], unique=False)
    op.drop_column('users', 'guide')
    op.drop_column('users', 'code')
    # ### end Alembic commands ###
