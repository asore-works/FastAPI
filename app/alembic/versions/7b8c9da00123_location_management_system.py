"""
app/alembic/versions/7b8c9da00123_location_management_system.py

拠点管理システム用のマイグレーション
拠点（ロケーション）とユーザー所属関連の管理機能を追加
"""

"""Location Management System
Revision ID: location_management_system
Revises: complete_user_model
Create Date: 2025-03-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text
# revision identifiers, used by Alembic.
revision: str = "location_management_system"
down_revision: Union[str, None] = "complete_user_model"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. 既存のユーザーテーブルからusernameフィールドを削除し、他の必要なフィールドを追加
    # ※注意: データ移行が必要な場合は、適切な移行スクリプトを実装してください
    # インデックスが存在する場合のみ削除する
    op.execute("DROP INDEX IF EXISTS ix_users_username")
    op.drop_column("users", "username")
    op.drop_column("users", "birth_date")
    op.drop_column("users", "phone_number")

    # 新しいフィールドを追加
    op.add_column(
        "users", sa.Column("full_name", sa.String(255), nullable=True, comment="氏名")
    )
    op.add_column(
        "users", sa.Column("role_id", sa.Integer(), nullable=True, comment="ロールID")
    )
    op.add_column(
        "users",
        sa.Column("employee_id", sa.String(50), nullable=True, comment="従業員ID"),
    )
    op.add_column(
        "users", sa.Column("department", sa.String(100), nullable=True, comment="部署")
    )
    op.add_column(
        "users", sa.Column("position", sa.String(100), nullable=True, comment="役職")
    )
    op.add_column(
        "users",
        sa.Column("mobile_phone", sa.String(50), nullable=True, comment="携帯電話番号"),
    )
    op.add_column(
        "users", sa.Column("address", sa.String(255), nullable=True, comment="住所")
    )
    op.add_column(
        "users",
        sa.Column(
            "profile_image_url",
            sa.String(255),
            nullable=True,
            comment="プロフィール画像URL",
        ),
    )
    op.add_column(
        "users",
        sa.Column("date_of_birth", sa.DateTime(), nullable=True, comment="生年月日"),
    )
    op.add_column(
        "users", sa.Column("hire_date", sa.DateTime(), nullable=True, comment="入社日")
    )
    op.add_column(
        "users",
        sa.Column(
            "last_login", sa.DateTime(), nullable=True, comment="最終ログイン日時"
        ),
    )

    # 新しいインデックスを作成
    op.create_index(
        "ix_users_name_search",
        "users",
        ["last_name", "first_name", "full_name"],
        unique=False,
    )
    op.create_index(
        "ix_users_department_position",
        "users",
        ["department", "position"],
        unique=False,
    )
    op.create_index("ix_users_employee_id", "users", ["employee_id"], unique=True)

    # 1. ロールテーブルの作成
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False, comment="ロール名"),
        sa.Column("description", sa.Text(), nullable=True, comment="説明"),
        sa.Column(
            "permissions", sa.Text(), nullable=False, comment="権限リスト（JSON文字列）"
        ),
        sa.Column(
            "is_system_role",
            sa.Boolean(),
            nullable=False,
            default=False,
            comment="システム定義ロールかどうか",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_roles_name"), "roles", ["name"], unique=True)

    # ユーザーテーブルの外部キー制約を追加
    op.create_foreign_key(
        "fk_users_role_id", "users", "roles", ["role_id"], ["id"], ondelete="SET NULL"
    )

    # 2. 拠点タイプの列挙型を作成
    connection = op.get_bind()
    try:
        # text() 関数を使用して SQL 文字列をラップ
        op.execute(
            text("CREATE TYPE locationtype AS ENUM ('headquarters', 'branch', 'office', 'warehouse', 'store', 'other')")
        )
    except Exception as e:
        # 「already exists」エラーは無視
        if "already exists" not in str(e):
            raise

    # 3. 拠点テーブルの作成
    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, comment="拠点名"),
        sa.Column("code", sa.String(length=20), nullable=False, comment="拠点コード"),
        sa.Column(
            "type",
            sa.Enum(
                "headquarters",
                "branch",
                "office",
                "warehouse",
                "store",
                "other",
                name="locationtype",
            ),
            nullable=False,
            comment="拠点タイプ",
        ),
        sa.Column("parent_id", sa.Integer(), nullable=True, comment="親拠点ID"),
        sa.Column(
            "postal_code", sa.String(length=20), nullable=True, comment="郵便番号"
        ),
        sa.Column(
            "prefecture", sa.String(length=50), nullable=True, comment="都道府県"
        ),
        sa.Column("city", sa.String(length=100), nullable=True, comment="市区町村"),
        sa.Column(
            "address1",
            sa.String(length=100),
            nullable=True,
            comment="住所1（町名・番地）",
        ),
        sa.Column(
            "address2",
            sa.String(length=100),
            nullable=True,
            comment="住所2（建物名・部屋番号）",
        ),
        sa.Column("phone", sa.String(length=50), nullable=True, comment="電話番号"),
        sa.Column("fax", sa.String(length=50), nullable=True, comment="FAX番号"),
        sa.Column(
            "email", sa.String(length=100), nullable=True, comment="メールアドレス"
        ),
        sa.Column(
            "business_hours", sa.String(length=255), nullable=True, comment="営業時間"
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="説明"),
        sa.Column(
            "manager_name", sa.String(length=100), nullable=True, comment="管理者名"
        ),
        sa.Column("capacity", sa.Integer(), nullable=True, comment="収容人数"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="アクティブ状態",
        ),
        sa.Column("latitude", sa.Float(), nullable=True, comment="緯度"),
        sa.Column("longitude", sa.Float(), nullable=True, comment="経度"),
        sa.Column("established_date", sa.DateTime(), nullable=True, comment="設立日"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="更新日時",
        ),
        sa.ForeignKeyConstraint(["parent_id"], ["locations.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # インデックスの作成
    op.create_index(op.f("ix_locations_code"), "locations", ["code"], unique=True)
    op.create_index(op.f("ix_locations_name"), "locations", ["name"], unique=False)
    op.create_index(
        op.f("ix_locations_parent_id"), "locations", ["parent_id"], unique=False
    )
    op.create_index(
        "ix_locations_address", "locations", ["prefecture", "city"], unique=False
    )
    op.create_index(
        "ix_locations_type_name", "locations", ["type", "name"], unique=False
    )

    # 4. ユーザー所属テーブルの作成
    op.create_table(
        "user_locations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="ユーザーID"),
        sa.Column("location_id", sa.Integer(), nullable=False, comment="拠点ID"),
        sa.Column(
            "is_primary",
            sa.Boolean(),
            nullable=False,
            server_default="true",
            comment="主所属かどうか",
        ),
        sa.Column(
            "position", sa.String(length=100), nullable=True, comment="拠点内での役職"
        ),
        sa.Column(
            "department", sa.String(length=100), nullable=True, comment="拠点内での部署"
        ),
        sa.Column(
            "start_date",
            sa.Date(),
            server_default=sa.text("current_date"),
            nullable=False,
            comment="所属開始日",
        ),
        sa.Column("end_date", sa.Date(), nullable=True, comment="所属終了日"),
        sa.Column("notes", sa.String(length=255), nullable=True, comment="備考"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="更新日時",
        ),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "location_id", "is_primary", name="uq_user_location_primary"
        ),
    )

    # インデックスの作成
    op.create_index(
        op.f("ix_user_locations_location_id"),
        "user_locations",
        ["location_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_locations_user_id"), "user_locations", ["user_id"], unique=False
    )


def downgrade() -> None:
    # 1. ユーザー所属テーブルの削除
    op.drop_index(op.f("ix_user_locations_user_id"), table_name="user_locations")
    op.drop_index(op.f("ix_user_locations_location_id"), table_name="user_locations")
    op.drop_table("user_locations")

    # 2. 拠点テーブルの削除
    op.drop_index("ix_locations_type_name", table_name="locations")
    op.drop_index("ix_locations_address", table_name="locations")
    op.drop_index(op.f("ix_locations_parent_id"), table_name="locations")
    op.drop_index(op.f("ix_locations_name"), table_name="locations")
    op.drop_index(op.f("ix_locations_code"), table_name="locations")
    op.drop_table("locations")

    # 3. 拠点タイプの列挙型を削除
    op.execute("DROP TYPE locationtype")

    # 4. ロールテーブルの削除
    op.drop_index(op.f("ix_roles_name"), table_name="roles")
    op.drop_table("roles")

    # 5. ユーザーテーブルから追加したフィールドとインデックスを削除
    op.drop_index("ix_users_name_search", table_name="users")
    op.drop_index("ix_users_department_position", table_name="users")
    op.drop_index("ix_users_employee_id", table_name="users")

    op.drop_column("users", "last_login")
    op.drop_column("users", "hire_date")
    op.drop_column("users", "date_of_birth")
    op.drop_column("users", "profile_image_url")
    op.drop_column("users", "address")
    op.drop_column("users", "mobile_phone")
    op.drop_column("users", "position")
    op.drop_column("users", "department")
    op.drop_column("users", "employee_id")
    op.drop_column("users", "role_id")
    op.drop_column("users", "full_name")

    # 6. 元のフィールドを復元
    op.add_column("users", sa.Column("phone_number", sa.String(20), nullable=True))
    op.add_column("users", sa.Column("birth_date", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("username", sa.String(50), nullable=False))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
