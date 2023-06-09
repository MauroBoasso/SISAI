"""empty message

Revision ID: 5950b9f9a099
Revises: f1803eb8cbf0
Create Date: 2023-03-17 21:04:35.295447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5950b9f9a099'
down_revision = 'f1803eb8cbf0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('role', sa.String(length=12), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('role')

    # ### end Alembic commands ###
