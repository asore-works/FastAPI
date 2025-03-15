"""Add user profile fields and remove full_name

Revision ID: 002_add_user_profile_fields
Revises: 001_initial_migration
Create Date: 2025-03-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_user_profile_fields'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 新しいフィールドを追加
    op.add_column('users', sa.Column('username', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('last_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('first_name', sa.String(100), nullable=True))
    op.add_column('users', sa.Column('birth_date', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('phone_number', sa.String(20), nullable=True))
    
    # emailからusernameの初期データを設定
    op.execute(
        """
        UPDATE users 
        SET username = SUBSTRING(email FROM 1 FOR POSITION('@' IN email) - 1)
        WHERE username IS NULL
        """
    )
    
    # full_nameがある場合は、そのデータをlast_nameに移行
    op.execute(
        """
        UPDATE users
        SET last_name = full_name
        WHERE full_name IS NOT NULL AND last_name IS NULL
        """
    )
    
    # usernameのNOT NULL制約を追加（初期データを設定した後）
    op.alter_column('users', 'username', nullable=False)
    
    # usernameにユニークインデックスを追加
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    
    # full_nameカラムを削除
    op.drop_column('users', 'full_name')


def downgrade() -> None:
    # full_nameカラムを復活
    op.add_column('users', sa.Column('full_name', sa.String(255), nullable=True))
    
    # last_nameとfirst_nameからfull_nameを復元（可能な場合）
    op.execute(
        """
        UPDATE users
        SET full_name = CONCAT(COALESCE(last_name, ''), ' ', COALESCE(first_name, ''))
        WHERE last_name IS NOT NULL OR first_name IS NOT NULL
        """
    )
    
    # ユニークインデックスを削除
    op.drop_index(op.f('ix_users_username'), table_name='users')
    
    # 追加したカラムを削除
    op.drop_column('users', 'phone_number')
    op.drop_column('users', 'birth_date')
    op.drop_column('users', 'first_name')
    op.drop_column('users', 'last_name')
    op.drop_column('users', 'username')