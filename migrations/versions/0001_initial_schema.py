"""Create the AI DevCoach schema in PostgreSQL."""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("terms_agreed_at", sa.Text(), nullable=False),
        sa.Column("terms_version", sa.Text(), nullable=False),
        sa.Column("privacy_agreed_at", sa.Text(), nullable=False),
        sa.Column("privacy_version", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("expires_at", sa.Text(), nullable=False),
    )
    op.create_table(
        "profiles",
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("nickname", sa.Text(), nullable=False),
        sa.Column("learning_goal", sa.Text(), nullable=False),
        sa.Column("self_assessed_level", sa.Text(), nullable=False),
        sa.Column("interest_skills", sa.Text(), nullable=False),
        sa.Column("weekly_hours", sa.Integer(), nullable=False),
        sa.Column("duration_weeks", sa.Integer(), nullable=False),
        sa.Column("github_username", sa.Text(), nullable=False, server_default=""),
        sa.Column("learning_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("assessment_level", sa.Text()),
        sa.Column("updated_at", sa.Text(), nullable=False),
    )
    op.create_table(
        "assessments",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("answers", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("result", sa.Text()),
        sa.Column("started_at", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.Text()),
    )
    op.create_index("ix_assessments_user_status_submitted", "assessments", ["user_id", "status", "submitted_at"])
    op.create_table(
        "plans",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("data", sa.Text(), nullable=False),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.Text(), nullable=False),
    )
    op.create_index("ix_plans_user_updated", "plans", ["user_id", "updated_at"])
    op.create_table(
        "task_progress",
        sa.Column("plan_id", sa.Text(), sa.ForeignKey("plans.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("task_id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="todo"),
        sa.Column("learning_start_date", sa.Text()),
        sa.Column("learning_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty_notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("learner_memo", sa.Text(), nullable=False, server_default=""),
        sa.Column("completed_at", sa.Text()),
        sa.Column("updated_at", sa.Text(), nullable=False),
        sa.CheckConstraint("status IN ('todo','in_progress','completed','blocked')", name="ck_task_progress_status"),
    )
    op.create_index("ix_task_progress_user_status", "task_progress", ["user_id", "status"])
    op.create_table(
        "learning_time_logs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("plan_id", sa.Text(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("learning_date", sa.Text(), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.Text(), nullable=False),
        sa.CheckConstraint("duration_minutes BETWEEN 1 AND 1440", name="ck_learning_time_minutes"),
    )
    op.create_index("ix_time_logs_plan_task_user", "learning_time_logs", ["plan_id", "task_id", "user_id"])
    op.create_index("ix_time_logs_plan_user_date", "learning_time_logs", ["plan_id", "user_id", "learning_date"])
    op.create_table(
        "task_submissions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("plan_id", sa.Text(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("github_url", sa.Text()),
        sa.Column("explanation", sa.Text()),
        sa.Column("status", sa.Text(), nullable=False, server_default="submitted"),
        sa.Column("submitted_at", sa.Text(), nullable=False),
    )
    op.create_index("ix_submissions_plan_task_user", "task_submissions", ["plan_id", "task_id", "user_id"])
    op.create_table(
        "learning_activity_logs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("plan_id", sa.Text(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("task_id", sa.Text(), nullable=False),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("old_value", sa.Text()),
        sa.Column("new_value", sa.Text()),
        sa.Column("created_at", sa.Text(), nullable=False),
    )
    op.create_index("ix_activity_plan_user_created", "learning_activity_logs", ["plan_id", "user_id", "created_at"])
    op.create_table(
        "plan_revision_requests",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("plan_id", sa.Text(), sa.ForeignKey("plans.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Text(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="requested"),
        sa.Column("created_at", sa.Text(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("plan_revision_requests")
    op.drop_index("ix_activity_plan_user_created", table_name="learning_activity_logs")
    op.drop_table("learning_activity_logs")
    op.drop_index("ix_submissions_plan_task_user", table_name="task_submissions")
    op.drop_table("task_submissions")
    op.drop_index("ix_time_logs_plan_user_date", table_name="learning_time_logs")
    op.drop_index("ix_time_logs_plan_task_user", table_name="learning_time_logs")
    op.drop_table("learning_time_logs")
    op.drop_index("ix_task_progress_user_status", table_name="task_progress")
    op.drop_table("task_progress")
    op.drop_index("ix_plans_user_updated", table_name="plans")
    op.drop_table("plans")
    op.drop_index("ix_assessments_user_status_submitted", table_name="assessments")
    op.drop_table("assessments")
    op.drop_table("profiles")
    op.drop_table("sessions")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_table("users")