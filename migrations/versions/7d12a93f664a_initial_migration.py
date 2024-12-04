"""initial migration

Revision ID: 7d12a93f664a
Revises: 
Create Date: 2024-12-04 11:34:46.405774

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '7d12a93f664a'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add unique constraint to student_id in academic_info
    op.create_unique_constraint('uq_academic_info_student_id', 'academic_info', ['student_id'])

    # Handle profile table changes
    with op.batch_alter_table('profile', schema=None) as batch_op:
        # Add id_number column
        batch_op.add_column(sa.Column('id_number', sa.String(length=20), nullable=True))
        
        # Add unique constraints
        batch_op.create_unique_constraint('uq_profile_phone_number', ['phone_number'])
    
    # Update existing records with a default value
    connection = op.get_bind()
    connection.execute(
        text("UPDATE profile SET id_number = 'LEGACY-' || id WHERE id_number IS NULL")
    )
    
    # Make id_number not nullable and add unique constraint
    with op.batch_alter_table('profile', schema=None) as batch_op:
        batch_op.alter_column('id_number',
                            existing_type=sa.String(length=20),
                            nullable=False)
        batch_op.create_unique_constraint('uq_profile_id_number', ['id_number'])


def downgrade():
    with op.batch_alter_table('profile', schema=None) as batch_op:
        batch_op.drop_constraint('uq_profile_id_number', type_='unique')
        batch_op.drop_constraint('uq_profile_phone_number', type_='unique')
        batch_op.drop_column('id_number')

    op.drop_constraint('uq_academic_info_student_id', 'academic_info', type_='unique')
