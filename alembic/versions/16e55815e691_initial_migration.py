"""initial migration

Revision ID: 16e55815e691
Revises:
Create Date: 2022-01-10 16:58:43.962071

"""
import fastapi_users_db_sqlalchemy
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy import types
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
from iris.commons.models import AgentParameters, ToolParameters

revision = "16e55815e691"
down_revision = None
branch_labels = None
depends_on = None


class PydanticType(types.TypeDecorator):
    impl = types.Unicode
    cache_ok = True

    def __init__(self, klass, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.klass = klass

    def process_bind_param(self, value, dialect):
        return value.json()

    def process_result_value(self, value, dialect):
        return self.klass.parse_raw(value)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "measurement",
        sa.Column(
            "tool",
            sa.Enum(
                "DiamondMiner",
                "Yarrp",
                "Ping",
                "Probes",
                name="tool",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("uuid", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("user_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("uuid"),
    )
    op.create_table(
        "user",
        sa.Column("id", fastapi_users_db_sqlalchemy.guid.GUID(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("hashed_password", sa.String(length=72), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("firstname", sa.String(), nullable=False),
        sa.Column("lastname", sa.String(), nullable=False),
        sa.Column("probing_enabled", sa.Boolean(), nullable=False),
        sa.Column("probing_limit", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=True)
    op.create_table(
        "measurement_agent",
        sa.Column(
            "tool_parameters",
            PydanticType(ToolParameters),
            nullable=True,
        ),
        sa.Column(
            "agent_parameters",
            PydanticType(AgentParameters),
            nullable=True,
        ),
        sa.Column(
            "state",
            sa.Enum(
                "AgentFailure",
                "Canceled",
                "Created",
                "Finished",
                "Ongoing",
                name="measurementagentstate",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("probing_rate", sa.Integer(), nullable=True),
        sa.Column("target_file", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "measurement_uuid", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("agent_uuid", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column(
            "probing_statistics", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
        sa.Column("start_time", sa.DateTime(), nullable=True),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["measurement_uuid"],
            ["measurement.uuid"],
        ),
        sa.PrimaryKeyConstraint("measurement_uuid", "agent_uuid"),
    )
    op.create_table(
        "oauth_account",
        sa.Column("id", fastapi_users_db_sqlalchemy.guid.GUID(), nullable=False),
        sa.Column("oauth_name", sa.String(length=100), nullable=False),
        sa.Column("access_token", sa.String(length=1024), nullable=False),
        sa.Column("expires_at", sa.Integer(), nullable=True),
        sa.Column("refresh_token", sa.String(length=1024), nullable=True),
        sa.Column("account_id", sa.String(length=320), nullable=False),
        sa.Column("account_email", sa.String(length=320), nullable=False),
        sa.Column("user_id", fastapi_users_db_sqlalchemy.guid.GUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_oauth_account_account_id"),
        "oauth_account",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_oauth_account_oauth_name"),
        "oauth_account",
        ["oauth_name"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_oauth_account_oauth_name"), table_name="oauth_account")
    op.drop_index(op.f("ix_oauth_account_account_id"), table_name="oauth_account")
    op.drop_table("oauth_account")
    op.drop_table("measurement_agent")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_table("measurement")
    # ### end Alembic commands ###