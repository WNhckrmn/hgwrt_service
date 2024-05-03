"""add resume table

Revision ID: 32e19c0926da
Revises: 020f658f272a
Create Date: 2024-04-26 20:28:19.659040

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32e19c0926da'
down_revision = '020f658f272a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Resume', schema=None) as batch_op:
        batch_op.add_column(sa.Column('filename', sa.String(length=100), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Resume', schema=None) as batch_op:
        batch_op.drop_column('filename')

    # ### end Alembic commands ###