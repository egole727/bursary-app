"""Add amount_allocated field and rename amount to amount_requested

Revision ID: 7ccfc531c72d
Revises: c65014097b72
Create Date: 2024-12-11 01:39:47.983544

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7ccfc531c72d"
down_revision = "c65014097b72"
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add amount_allocated column
    op.add_column(
        "application", sa.Column("amount_allocated", sa.Float(), nullable=True)
    )

    # 2. Add amount_requested column as nullable first
    op.add_column(
        "application", sa.Column("amount_requested", sa.Float(), nullable=True)
    )

    # 3. Copy data from amount to amount_requested
    op.execute("UPDATE application SET amount_requested = amount")

    # 4. Make amount_requested not nullable
    op.alter_column(
        "application", "amount_requested", existing_type=sa.Float(), nullable=False
    )

    # 5. Drop the old amount column
    op.drop_column("application", "amount")


def downgrade():
    # 1. Add back the amount column
    op.add_column("application", sa.Column("amount", sa.Float(), nullable=True))

    # 2. Copy data back
    op.execute("UPDATE application SET amount = amount_requested")

    # 3. Drop the new columns
    op.drop_column("application", "amount_allocated")
    op.drop_column("application", "amount_requested")
