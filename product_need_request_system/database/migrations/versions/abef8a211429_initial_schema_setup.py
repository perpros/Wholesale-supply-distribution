"""Initial schema setup

Revision ID: abef8a211429
Revises:
Create Date: 2025-06-17T09:09:01.428740

"""
from alembic import op
import sqlalchemy as sa

from app.models.enums import ProductTypeEnum, RequestStatusEnum, ProposalStatusEnum

# revision identifiers, used by Alembic.
revision = 'abef8a211429'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types for PostgreSQL before creating tables that use them
    op.execute("CREATE TYPE producttypeenum AS ENUM ('SOFTWARE_LICENSE', 'HARDWARE', 'CONSULTING_SERVICE', 'OTHER')")
    op.execute("CREATE TYPE requeststatusenum AS ENUM ('SUBMITTED', 'APPROVED', 'REJECTED', 'PENDING_EVALUATION', 'CLOSED_FULFILLED', 'CLOSED_UNFULFILLED', 'CANCELLED', 'EXPIRED')")
    op.execute("CREATE TYPE proposalstatusenum AS ENUM ('SUBMITTED')")

    op.create_table('roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_id'), 'roles', ['id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=True)

    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    op.create_table('user_role_association',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'role_id')
    )

    op.create_table('requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_type', sa.Enum(ProductTypeEnum, name='producttypeenum', create_type=False), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('promised_delivery_date', sa.DateTime(), nullable=False),
        sa.Column('expiration_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum(RequestStatusEnum, name='requeststatusenum', create_type=False), server_default=RequestStatusEnum.SUBMITTED.value, nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_requests_id'), 'requests', ['id'], unique=False)
    op.create_index(op.f('ix_requests_status'), 'requests', ['status'], unique=False)

    op.create_table('proposals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum(ProposalStatusEnum, name='proposalstatusenum', create_type=False), server_default=ProposalStatusEnum.SUBMITTED.value, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('request_id', 'supplier_id', name='uq_proposal_request_supplier')
    )
    op.create_index(op.f('ix_proposals_id'), 'proposals', ['id'], unique=False)

    op.create_table('request_status_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum(RequestStatusEnum, name='requeststatusenum', create_type=False), nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('changed_by_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_request_status_history_id'), 'request_status_history', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_request_status_history_id'), table_name='request_status_history')
    op.drop_table('request_status_history')
    op.drop_index(op.f('ix_proposals_id'), table_name='proposals')
    op.drop_table('proposals')
    op.drop_index(op.f('ix_requests_status'), table_name='requests')
    op.drop_index(op.f('ix_requests_id'), table_name='requests')
    op.drop_table('requests')
    op.drop_table('user_role_association')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_roles_name'), table_name='roles')
    op.drop_index(op.f('ix_roles_id'), table_name='roles')
    op.drop_table('roles')

    # Drop ENUM types for PostgreSQL
    op.execute("DROP TYPE proposalstatusenum")
    op.execute("DROP TYPE requeststatusenum")
    op.execute("DROP TYPE producttypeenum")
    # ### end Alembic commands ###
