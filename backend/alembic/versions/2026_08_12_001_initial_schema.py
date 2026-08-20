"""Initial schema migration

Revision ID: 2026_08_12_001
Revises: None
Create Date: 2026-08-12 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.sql.sqltypes as satypes


# revision identifiers, used by Alembic.
revision = "2026_08_12_001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TYPE public."organization_plan_enum" AS ENUM('free', 'starter', 'pro', 'enterprise');
    """)

    op.execute("""
        CREATE TYPE public."user_role_enum" AS ENUM('owner', 'admin', 'member', 'viewer');
    """)

    op.execute("""
        CREATE TYPE public."dataset_status_enum" AS ENUM('uploading', 'processing', 'ready', 'error');
    """)

    op.execute("""
        CREATE TYPE public."report_status_enum" AS ENUM('queued', 'generating', 'completed', 'failed');
    """)

    op.execute("""
        CREATE TYPE public."chat_message_role_enum" AS ENUM('user', 'assistant', 'system');
    """)

    op.execute("""
        CREATE TYPE public."forecast_model_type_enum" AS ENUM('prophet', 'ets', 'arima');
    """)

    # organizations table
    op.create_table(
        "organizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("plan", sa.String(50), server_default="free"),
        sa.Column("stripe_customer_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="member"),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # datasets table
    op.create_table(
        "datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("uploaded_by", sa.String(36), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(10), server_default="csv"),
        sa.Column("file_path", sa.String(512), nullable=False),
        sa.Column("schema_json", satypes.JSON(), nullable=True),
        sa.Column("row_count", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(20), server_default="uploading"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )

    # reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("report_type", sa.String(50), server_default="auto_summary"),
        sa.Column("narrative_text", sa.Text(), nullable=True),
        sa.Column("computed_stats_json", sa.Text(), nullable=True),
        sa.Column("charts_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("export_format", sa.String(10), nullable=True),
        sa.Column("export_result", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("generated_at", sa.DateTime(), nullable=True),
    )

    # chat_sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # chat_messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("chart_data_json", sa.Text(), nullable=True),
        sa.Column("query_executed", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # forecast_jobs table
    op.create_table(
        "forecast_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("dataset_id", sa.String(36), nullable=False),
        sa.Column("created_by", sa.String(36), nullable=False),
        sa.Column("target_column", sa.String(255), nullable=False),
        sa.Column("date_column", sa.String(255), nullable=False),
        sa.Column("horizon_periods", sa.Integer(), server_default="12"),
        sa.Column("model_type", sa.String(20), server_default="prophet"),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), server_default="queued"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # scheduled_reports table (post-MVP)
    op.create_table(
        "scheduled_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("org_id", sa.String(36), nullable=False),
        sa.Column("report_config_json", sa.JSON(), nullable=False),
        sa.Column("frequency", sa.String(20), server_default="weekly"),
        sa.Column("recipients", sa.JSON(), server_default="[]"),
        sa.Column("next_run_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index("ix_organizations_slug", "organizations", ["slug"], unique=True)
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_org_id", "users", ["org_id"])
    op.create_index("ix_datasets_org_id", "datasets", ["org_id"])
    op.create_index("ix_datasets_status", "datasets", ["status"])
    op.create_index("ix_reports_org_id", "reports", ["org_id"])
    op.create_index("ix_reports_dataset_id", "reports", ["dataset_id"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_index("ix_chat_sessions_org_id", "chat_sessions", ["org_id"])
    op.create_index("ix_chat_sessions_dataset_id", "chat_sessions", ["dataset_id"])
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"])
    op.create_index("ix_forecast_jobs_org_id", "forecast_jobs", ["org_id"])
    op.create_index("ix_forecast_jobs_dataset_id", "forecast_jobs", ["dataset_id"])
    op.create_index("ix_forecast_jobs_status", "forecast_jobs", ["status"])
    op.create_index("ix_scheduled_reports_org_id", "scheduled_reports", ["org_id"])
    op.create_index("ix_scheduled_reports_next_run_at", "scheduled_reports", ["next_run_at"])


def downgrade() -> None:
    op.drop_index("ix_scheduled_reports_next_run_at", table_name="scheduled_reports")
    op.drop_index("ix_scheduled_reports_org_id", table_name="scheduled_reports")
    op.drop_index("ix_forecast_jobs_status", table_name="forecast_jobs")
    op.drop_index("ix_forecast_jobs_dataset_id", table_name="forecast_jobs")
    op.drop_index("ix_forecast_jobs_org_id", table_name="forecast_jobs")
    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("ix_chat_sessions_dataset_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_org_id", table_name="chat_sessions")
    op.drop_index("ix_reports_status", table_name="reports")
    op.drop_index("ix_reports_dataset_id", table_name="reports")
    op.drop_index("ix_reports_org_id", table_name="reports")
    op.drop_index("ix_datasets_status", table_name="datasets")
    op.drop_index("ix_datasets_org_id", table_name="datasets")
    op.drop_index("ix_users_email", "users")
    op.drop_index("ix_users_org_id", table_name="users")
    op.drop_index("ix_organizations_slug", "organizations")

    op.drop_table("scheduled_reports")
    op.drop_table("forecast_jobs")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("reports")
    op.drop_table("datasets")
    op.drop_table("users")
    op.drop_table("organizations")

    op.execute("DROP TYPE IF EXISTS public."organization_plan_enum")
    op.execute("DROP TYPE IF EXISTS public."user_role_enum")
    op.execute("DROP TYPE IF EXISTS public."dataset_status_enum")
    op.execute("DROP TYPE IF EXISTS public."report_status_enum")
    op.execute("DROP TYPE IF EXISTS public."chat_message_role_enum")
    op.execute("DROP TYPE IF EXISTS public."forecast_model_type_enum")