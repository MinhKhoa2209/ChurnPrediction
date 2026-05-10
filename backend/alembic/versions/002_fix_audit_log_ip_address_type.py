
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

                                        
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        'audit_logs',
        'ip_address',
        type_=sa.String(45),
        existing_type=postgresql.INET(),
        existing_nullable=True,
        postgresql_using='ip_address::text'
    )


def downgrade() -> None:
    op.alter_column(
        'audit_logs',
        'ip_address',
        type_=postgresql.INET(),
        existing_type=sa.String(45),
        existing_nullable=True,
        postgresql_using='ip_address::inet'
    )
