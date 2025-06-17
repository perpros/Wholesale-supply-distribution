"""initial_migration

Revision ID: 2238fd522d60
Revises:
Create Date: 2025-06-17 08:32:08.962180

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Enum definitions from app.models
# These need to be created as types in PostgreSQL
user_role_enum = postgresql.ENUM('END_USER', 'SUPPLIER', 'ADMIN', name='user_role_enum', create_type=False)
request_status_enum = postgresql.ENUM('SUBMITTED', 'ACCEPTED', 'APPROVED', 'REJECTED', 'CANCELLED', 'RESUBMITTED', 'EXPIRED', 'CLOSED', name='request_status_enum', create_type=False)

# revision identifiers, used by Alembic.
revision: str = '2238fd522d60'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create ENUM types
    user_role_enum.create(op.get_bind(), checkfirst=True)
    request_status_enum.create(op.get_bind(), checkfirst=True)

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('role', user_role_enum, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)

    # Create requests table
    op.create_table(
        'requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_type', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('promised_delivery_date', sa.Date(), nullable=False),
        sa.Column('expiration_date', sa.Date(), nullable=False),
        sa.Column('status', request_status_enum, nullable=False, server_default='SUBMITTED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), onupdate=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('quantity >= 1', name='check_request_quantity')
    )
    op.create_index(op.f('ix_requests_id'), 'requests', ['id'], unique=False)

    # Create proposals table
    op.create_table(
        'proposals',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.ForeignKeyConstraint(['supplier_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('supplier_id', 'request_id', name='uq_supplier_request'),
        sa.CheckConstraint('quantity >= 1', name='check_proposal_quantity')
    )
    op.create_index(op.f('ix_proposals_id'), 'proposals', ['id'], unique=False)

    # Create request_status_history table
    op.create_table(
        'request_status_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('status', request_status_enum, nullable=False),
        sa.Column('changed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('changed_by_user_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['changed_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_request_status_history_id'), 'request_status_history', ['id'], unique=False)

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('request_id', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('read', sa.Boolean(), server_default=sa.false(), nullable=True),
        sa.ForeignKeyConstraint(['request_id'], ['requests.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')
    op.drop_index(op.f('ix_request_status_history_id'), table_name='request_status_history')
    op.drop_table('request_status_history')
    op.drop_index(op.f('ix_proposals_id'), table_name='proposals')
    op.drop_table('proposals')
    op.drop_index(op.f('ix_requests_id'), table_name='requests')
    op.drop_table('requests')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # Drop ENUM types
    request_status_enum.drop(op.get_bind(), checkfirst=True)
    user_role_enum.drop(op.get_bind(), checkfirst=True)
