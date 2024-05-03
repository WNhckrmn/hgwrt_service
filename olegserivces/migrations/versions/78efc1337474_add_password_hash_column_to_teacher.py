"""Add password_hash column to Teacher

Revision ID: 78efc1337474
Revises: 
Create Date: 2024-04-08 02:52:20.993168

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '78efc1337474'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=100), nullable=False))

    with op.batch_alter_table('teacher', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=100), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('teacher', schema=None) as batch_op:
        batch_op.drop_column('password_hash')

    with op.batch_alter_table('student', schema=None) as batch_op:
        batch_op.drop_column('password_hash')

    # ### end Alembic commands ###