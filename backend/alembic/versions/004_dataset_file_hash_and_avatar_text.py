from alembic import op
import sqlalchemy as sa


revision = "004_dataset_hash_avatar"
down_revision = "003_auth_security_hardening"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("datasets", sa.Column("file_hash", sa.String(length=64), nullable=True))
    op.create_index(op.f("ix_datasets_file_hash"), "datasets", ["file_hash"], unique=False)
    op.alter_column(
        "users",
        "avatar",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "avatar",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.drop_index(op.f("ix_datasets_file_hash"), table_name="datasets")
    op.drop_column("datasets", "file_hash")
