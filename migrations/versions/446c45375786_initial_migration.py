"""initial migration

Revision ID: 446c45375786
Revises: 7d12a93f664a
Create Date: 2024-12-04 11:53:39.599901

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "446c45375786"
down_revision = "7d12a93f664a"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("profile", schema=None) as batch_op:
        batch_op.drop_constraint("profile_uq_profile_id_number_key", type_="unique")
        batch_op.drop_column("uq_profile_id_number")

    # Add username column to user table
    op.add_column("user", sa.Column("username", sa.String(64), unique=True))

    # Update existing users to have a username based on their email
    op.execute(
        """
        UPDATE "user" 
        SET username = SPLIT_PART(email, '@', 1)
        WHERE username IS NULL
    """
    )

    # Make username not nullable after setting default values
    op.alter_column("user", "username", existing_type=sa.String(64), nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("profile", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "uq_profile_id_number",
                sa.VARCHAR(length=20),
                autoincrement=False,
                nullable=False,
            )
        )
        batch_op.create_unique_constraint(
            "profile_uq_profile_id_number_key", ["uq_profile_id_number"]
        )

    op.drop_column("user", "username")

    # ### end Alembic commands ###
