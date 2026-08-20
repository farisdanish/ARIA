"""add demo_visit_log table

Revision ID: a1b2c3d4e5f6
Revises: 6ebe711cac35
Create Date: 2026-08-20 21:52:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '6ebe711cac35'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'demo_visit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('Timestamp', sa.DateTime(), nullable=False),
        sa.Column('GuestID', sa.String(length=50), nullable=False),
        sa.Column('Action', sa.String(length=50), nullable=False),
        sa.Column('Message', sa.String(length=255), nullable=False),
        sa.Column('IPAddress', sa.String(length=45), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('demo_visit_log')
