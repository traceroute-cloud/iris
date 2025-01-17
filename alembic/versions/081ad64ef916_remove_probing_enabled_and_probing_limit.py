"""remove probing_enabled and probing_limit

Revision ID: 081ad64ef916
Revises: 1d8077da4ad6
Create Date: 2023-11-12 17:02:18.143919

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "081ad64ef916"
down_revision = "1d8077da4ad6"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("user", "probing_enabled")
    op.drop_column("user", "probing_limit")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "user",
        sa.Column("probing_limit", sa.INTEGER(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "user",
        sa.Column("probing_enabled", sa.BOOLEAN(), autoincrement=False, nullable=False),
    )
    # ### end Alembic commands ###
