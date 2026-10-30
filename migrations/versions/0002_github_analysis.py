"""Store GitHub project analysis runs."""

from alembic import op
import sqlalchemy as sa


revision = "0002_github_analysis"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_analysis_runs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner", sa.Text(), nullable=False),
        sa.Column("repo_name", sa.Text(), nullable=False),
        sa.Column("repo_url", sa.Text(), nullable=False),
        sa.Column("branch", sa.Text(), nullable=False),
        sa.Column("commit_sha", sa.Text(), nullable=False),
        sa.Column("result", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_index(
        "ix_github_analysis_user_created",
        "github_analysis_runs",
        ["user_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_github_analysis_user_created", table_name="github_analysis_runs")
    op.drop_table("github_analysis_runs")