import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user import UserService
from app.core.exceptions import ConflictException, NotFoundException
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from datetime import date


class TestUserService:
    """UserServiceのテストクラス"""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session: AsyncSession):
        """ユーザー作成の正常系テスト"""
        # テスト用ユーザーデータ - Pydanticモデルを使用
        user_in = UserCreate(
            email="test_create@example.com",
            username="test_create_user",  # usernameを追加
            password="testpassword",
            last_name="Test",  # full_nameの代わりにlast_nameを使用
            first_name="User",  # first_nameを追加
            is_superuser=False,
        )
        
        # ユーザー作成
        user = await UserService.create(db_session, obj_in=user_in)
        
        # 検証
        assert user is not None
        assert user.email == user_in.email
        assert user.username == user_in.username
        assert user.last_name == user_in.last_name
        assert user.first_name == user_in.first_name
        assert user.is_superuser == user_in.is_superuser
        assert user.hashed_password != user_in.password

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, db_session: AsyncSession):
        """重複メールアドレスによるユーザー作成の異常系テスト"""
        # テスト用ユーザーデータ - Pydanticモデルを使用
        user_in = UserCreate(
            email="test_duplicate@example.com",
            password="testpassword",
            full_name="Test User",
        )

        # 最初のユーザー作成
        await UserService.create(db_session, obj_in=user_in)

        # 同じメールアドレスで2回目の作成を試みる
        with pytest.raises(ConflictException):
            await UserService.create(db_session, obj_in=user_in)

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session: AsyncSession, normal_user: User):
        """IDによるユーザー取得テスト"""
        # ユーザー取得
        user = await UserService.get(db_session, normal_user.id)

        # 検証
        assert user is not None
        assert user.id == normal_user.id
        assert user.email == normal_user.email

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, db_session: AsyncSession, normal_user: User):
        """メールアドレスによるユーザー取得テスト"""
        # ユーザー取得
        user = await UserService.get_by_email(db_session, normal_user.email)

        # 検証
        assert user is not None
        assert user.id == normal_user.id
        assert user.email == normal_user.email

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, db_session: AsyncSession):
        """存在しないユーザーの取得テスト"""
        # 存在しないIDでユーザー取得
        user = await UserService.get(db_session, 9999)

        # 検証
        assert user is None

    @pytest.mark.asyncio
    async def test_update_user(self, db_session: AsyncSession, normal_user: User):
        """ユーザー情報更新テスト"""
        # 更新前のパスワードハッシュを保存
        old_hash = normal_user.hashed_password

        # 更新データ - Pydanticモデルを使用
        update_data = UserUpdate(
            full_name="Updated Name",
            password="newpassword123",
        )

        # ユーザー更新
        updated_user = await UserService.update(db_session, normal_user, update_data)

        # 検証
        assert updated_user is not None
        assert updated_user.id == normal_user.id
        assert updated_user.full_name == update_data.full_name
        # 更新前のハッシュ値と新しいハッシュ値が異なることを確認
        assert updated_user.hashed_password != old_hash

    @pytest.mark.asyncio
    async def test_authenticate_user(self, db_session: AsyncSession):
        """ユーザー認証テスト"""
        # テスト用ユーザーデータ
        email = "auth_test@example.com"
        password = "authpassword123"

        # ユーザー作成 - Pydanticモデルを使用
        user_in = UserCreate(
            email=email,
            password=password,
            full_name="Auth Test User",
        )

        await UserService.create(db_session, obj_in=user_in)

        # 正しい認証情報でログイン
        authenticated_user = await UserService.authenticate(
            db_session, email=email, password=password
        )

        # 検証
        assert authenticated_user is not None
        assert authenticated_user.email == email

        # 誤ったパスワードでログイン
        wrong_auth_user = await UserService.authenticate(
            db_session, email=email, password="wrongpassword"
        )

        # 検証
        assert wrong_auth_user is None

        # 存在しないメールアドレスでログイン
        nonexistent_user = await UserService.authenticate(
            db_session, email="nonexistent@example.com", password=password
        )

        # 検証
        assert nonexistent_user is None

    @pytest.mark.asyncio
    async def test_delete_user(self, db_session: AsyncSession):
        """ユーザー削除テスト"""
        # テスト用ユーザー作成 - Pydanticモデルを使用
        user_in = UserCreate(
            email="delete_test@example.com",
            password="deletepassword",
            full_name="Delete Test User",
        )

        user = await UserService.create(db_session, obj_in=user_in)

        # ユーザー削除
        deleted_user = await UserService.delete(db_session, user.id)

        # 検証
        assert deleted_user is not None
        assert deleted_user.id == user.id

        # 削除されたことを確認
        user_after_delete = await UserService.get(db_session, user.id)
        assert user_after_delete is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_user(self, db_session: AsyncSession):
        """存在しないユーザーの削除テスト"""
        # 存在しないIDでユーザー削除
        with pytest.raises(NotFoundException):
            await UserService.delete(db_session, 9999)

    @pytest.mark.asyncio
    async def test_get_multi_users(
        self, db_session: AsyncSession, normal_user: User, superuser: User
    ):
        """複数ユーザーの取得テスト"""
        # 複数ユーザー取得
        users = await UserService.get_multi(db_session)

        # 検証（最低でも2ユーザーは存在する）
        assert len(users) >= 2

        # アクティブユーザーのみ取得
        active_users = await UserService.get_multi(db_session, is_active=True)

        # 検証
        assert len(active_users) >= 2
        for user in active_users:
            assert user.is_active is True


@pytest.mark.asyncio
async def test_create_user_with_new_fields(db_session: AsyncSession):
    """拡張フィールド付きでのユーザー作成の正常系テスト"""
    # テスト用ユーザーデータ
    birth_date = date(1990, 1, 15)
    user_in = UserCreate(
        email="test_extended@example.com",
        username="test_user",
        password="testpassword",
        last_name="山田",
        first_name="太郎",
        birth_date=birth_date,
        phone_number="090-1234-5678",
        is_superuser=False,
    )
    
    # ユーザー作成
    user = await UserService.create(db_session, obj_in=user_in)
    
    # 検証
    assert user is not None
    assert user.email == user_in.email
    assert user.username == user_in.username
    assert user.last_name == user_in.last_name
    assert user.first_name == user_in.first_name
    assert user.birth_date == birth_date
    assert user.phone_number == user_in.phone_number
    assert user.is_superuser == user_in.is_superuser
    assert user.hashed_password != user_in.password  # パスワードがハッシュ化されていることを確認

@pytest.mark.asyncio
async def test_full_name_property(db_session: AsyncSession):
    """full_nameプロパティの動作確認テスト"""
    # ケース1: 姓と名の両方がある場合
    user_with_full_name = UserCreate(
        email="fullname_test@example.com",
        username="fullname_user",
        password="testpassword",
        last_name="佐藤",
        first_name="花子",
    )
    user1 = await UserService.create(db_session, obj_in=user_with_full_name)
    assert user1.full_name == "佐藤 花子"

    # ケース2: 姓のみがある場合
    user_with_last_name = UserCreate(
        email="lastname_test@example.com",
        username="lastname_user",
        password="testpassword",
        last_name="田中",
    )
    user2 = await UserService.create(db_session, obj_in=user_with_last_name)
    assert user2.full_name == "田中"

    # ケース3: 名のみがある場合
    user_with_first_name = UserCreate(
        email="firstname_test@example.com",
        username="firstname_user",
        password="testpassword",
        first_name="次郎",
    )
    user3 = await UserService.create(db_session, obj_in=user_with_first_name)
    assert user3.full_name == "次郎"

    # ケース4: 姓も名もない場合
    user_without_name = UserCreate(
        email="noname_test@example.com",
        username="noname_user",
        password="testpassword",
    )
    user4 = await UserService.create(db_session, obj_in=user_without_name)
    assert user4.full_name == ""


@pytest.mark.asyncio
async def test_username_uniqueness(db_session: AsyncSession):
    """ユーザー名の一意性テスト"""
    # 1人目のユーザーを作成
    user1_in = UserCreate(
        email="user1@example.com",
        username="unique_username",
        password="password123",
    )
    await UserService.create(db_session, obj_in=user1_in)

    # 同じユーザー名で2人目のユーザーを作成しようとする（失敗するはず）
    user2_in = UserCreate(
        email="user2@example.com",
        username="unique_username",  # 同じユーザー名
        password="password456",
    )

    with pytest.raises(ConflictException):
        await UserService.create(db_session, obj_in=user2_in)
