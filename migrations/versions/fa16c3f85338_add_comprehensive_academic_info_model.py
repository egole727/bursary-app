"""Add comprehensive academic info model

Revision ID: fa16c3f85338
Revises: 5222711301e8
Create Date: 2024-12-10 23:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'fa16c3f85338'
down_revision = '5222711301e8'
branch_labels = None
depends_on = None

def upgrade():
    # Add only the new columns
    with op.batch_alter_table('academic_info', schema=None) as batch_op:
        # New columns being added
        batch_op.add_column(sa.Column('institution_name', sa.String(255), nullable=True))
        batch_op.add_column(sa.Column('education_level', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('current_grade', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('school_account_number', sa.String(50), nullable=True))
        batch_op.add_column(sa.Column('bank_name', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('bank_branch', sa.String(100), nullable=True))

    # Update existing records with default values
    op.execute(text("""
        UPDATE academic_info 
        SET institution_name = 'Not Provided',
            education_level = 'Not Specified',
            school_account_number = 'Not Provided',
            bank_name = 'Not Provided',
            bank_branch = 'Not Provided',
            created_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE institution_name IS NULL
    """))

    # Now make the required columns NOT NULL
    with op.batch_alter_table('academic_info', schema=None) as batch_op:
        batch_op.alter_column('institution_name',
                            existing_type=sa.String(255),
                            nullable=False)
        batch_op.alter_column('education_level',
                            existing_type=sa.String(50),
                            nullable=False)
        batch_op.alter_column('school_account_number',
                            existing_type=sa.String(50),
                            nullable=False)
        batch_op.alter_column('bank_name',
                            existing_type=sa.String(100),
                            nullable=False)
        batch_op.alter_column('bank_branch',
                            existing_type=sa.String(100),
                            nullable=False)

def downgrade():
    with op.batch_alter_table('academic_info', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('bank_branch')
        batch_op.drop_column('bank_name')
        batch_op.drop_column('school_account_number')
        batch_op.drop_column('current_grade')
        batch_op.drop_column('course')
        batch_op.drop_column('education_level')
        batch_op.drop_column('institution_name')