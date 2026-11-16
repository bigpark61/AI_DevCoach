"""Persist AI coach conversation history."""

from alembic import op
import sqlalchemy as sa


revision = "0004_agent_chat_history"
down_revision = "0003_password_reset_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_chat_messages",
        sa.Column("id", sa.BigInteger().with_variant(sa.Integer(), "sqlite"), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sources_json", sa.Text(), server_default="[]", nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="ck_agent_chat_messages_role"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_agent_chat_messages_user_id_id",
        "agent_chat_messages",
        ["user_id", "id"],
    )


def downgrade() -> None:
    op.drop_index("ix_agent_chat_messages_user_id_id", table_name="agent_chat_messages")
    op.drop_table("agent_chat_messages")
