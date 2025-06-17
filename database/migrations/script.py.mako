"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | JINJA_ESCAPE}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision = '${up_revision}'
down_revision = ${down_revision | JINJA_ESCAPE | repr}
branch_labels = ${branch_labels | JINJA_ESCAPE | repr}
depends_on = ${depends_on | JINJA_ESCAPE | repr}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
