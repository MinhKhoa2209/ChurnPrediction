"""Fix audit_log ip_address type from INET to VARCHAR

Revision ID: 002
Revises: 001
Create Date: 2025-05-05 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change ip_address column from INET to VARCHAR(45) for better compatibility"""
    # Change column type from INET to VARCHAR(45)
    op.alter_column(
        'audit_logs',
        'ip_address',
        type_=sa.String(45),
        existing_type=postgresql.INET(),
        existing_nullable=True,
        postgresql_using='ip_address::text'
    )


def downgrade() -> None:
    """Revert ip_address column back to INET type"""
    op.alter_column(
        'audit_logs',
        'ip_address',
        type_=postgresql.INET(),
        existing_type=sa.String(45),
        existing_nullable=True,
        postgresql_using='ip_address::inet'
    )
