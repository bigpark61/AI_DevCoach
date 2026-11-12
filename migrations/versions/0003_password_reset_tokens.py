"""Add expiring password reset tokens."""

from alembic import op
import sqlalchemy as sa


revision = "0003_password_reset_tokens"
down_revision = "0002_github_analysis"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_tokens",
        sa.Column("token_hash", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
        sa.Column("used_at", sa.Text()),
    )
    op.create_index("ix_password_reset_tokens_user", "password_reset_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_password_reset_tokens_user", table_name="password_reset_tokens")
    op.drop_table("password_reset_tokens")