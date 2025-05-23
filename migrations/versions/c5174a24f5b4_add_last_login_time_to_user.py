"""Add last_login_time to User

Revision ID: c5174a24f5b4
Revises: 0b9b5b2ca0c4
Create Date: 2025-05-07 23:35:55.393879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5174a24f5b4'
down_revision = '0b9b5b2ca0c4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('last_login_time', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('last_login_time')

    # ### end Alembic commands ###
