"""Audit log table migration.

Adds the audit_logs table for tracking all significant operations
with org_id scoping for multi-tenant audit trails.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2026_08_12_002"
down_revision = "2026_08_12_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create the audit_logs table."""
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(12), primary_key=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(500), nullable=False),
        sa.Column("org_id", sa.String(50), nullable=True, index=True),
        sa.Column("user_id", sa.String(50), nullable=True, index=True),
        sa.Column("request_id", sa.String(12), unique=True, nullable=False, index=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.String(500), nullable=True),
        sa.Column("status_code", sa.Integer, nullable=True),
        sa.Column("response_time_ms", sa.Integer, nullable=True),
        sa.Column("sensitive_data_detected", sa.Boolean, nullable=False, server_default=sa.text("0")),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("1")),
    )


def downgrade() -> None:
    """Drop the audit_logs table."""
    op.drop_table("audit_logs")