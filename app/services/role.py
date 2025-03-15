from enum import Enum
from typing import List, Dict
from fastapi import Depends, HTTPException, status

from app.api.dependencies.auth import get_current_active_user
from app.core.exceptions import ForbiddenException
from app.models.user import User

class Permission(str, Enum):
    # ユーザー管理関連
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    MANAGE_USERS = "manage:users"
    
    # ロール関連
    READ_ROLES = "read:roles"
    WRITE_ROLES = "write:roles"
    
    # 拠点関連
    READ_LOCATIONS = "read:locations"
    WRITE_LOCATIONS = "write:locations"
    MANAGE_LOCATIONS = "manage:locations"
    
    # カタログ関連
    READ_CATALOG = "read:catalog"
    WRITE_CATALOG = "write:catalog"
    MANAGE_CATALOG = "manage:catalog"
    
    # 在庫関連
    READ_INVENTORY = "read:inventory"
    WRITE_INVENTORY = "write:inventory"
    MANAGE_INVENTORY = "manage:inventory"
    
    # スケジュール関連
    READ_SCHEDULES = "read:schedules"
    WRITE_SCHEDULES = "write:schedules"
    MANAGE_SCHEDULES = "manage:schedules"
    
    # 顧客関連
    READ_CLIENTS = "read:clients"
    WRITE_CLIENTS = "write:clients"
    MANAGE_CLIENTS = "manage:clients"
    
    # 自分のリソースに対する権限
    READ_OWN = "read:own"
    WRITE_OWN = "write:own"
    
    # 管理者権限
    ADMIN = "admin"

# システムロールと関連権限の定義
SYSTEM_ROLES = {
    "superuser": {
        "name": "スーパーユーザー",
        "description": "システム管理者。すべての権限を持つ。",
        "permissions": [p.value for p in Permission]
    },
    "general_manager": {
        "name": "統括マネージャー",
        "description": "統括マネージャー。ほとんどの権限を持つが、システム設定は変更できない。",
        "permissions": [
            Permission.READ_USERS.value, Permission.WRITE_USERS.value,
            Permission.READ_ROLES.value,
            Permission.READ_LOCATIONS.value, Permission.WRITE_LOCATIONS.value, Permission.MANAGE_LOCATIONS.value,
            Permission.READ_CATALOG.value, Permission.WRITE_CATALOG.value, Permission.MANAGE_CATALOG.value,
            Permission.READ_INVENTORY.value, Permission.WRITE_INVENTORY.value, Permission.MANAGE_INVENTORY.value,
            Permission.READ_SCHEDULES.value, Permission.WRITE_SCHEDULES.value, Permission.MANAGE_SCHEDULES.value,
            Permission.READ_CLIENTS.value, Permission.WRITE_CLIENTS.value, Permission.MANAGE_CLIENTS.value,
            Permission.READ_OWN.value, Permission.WRITE_OWN.value
        ]
    },
    "area_manager": {
        "name": "エリアマネージャー",
        "description": "エリアマネージャー。担当エリアに対する管理権限を持つ。",
        "permissions": [
            Permission.READ_USERS.value,
            Permission.READ_LOCATIONS.value, Permission.WRITE_LOCATIONS.value,
            Permission.READ_CATALOG.value,
            Permission.READ_INVENTORY.value, Permission.WRITE_INVENTORY.value,
            Permission.READ_SCHEDULES.value, Permission.WRITE_SCHEDULES.value, Permission.MANAGE_SCHEDULES.value,
            Permission.READ_CLIENTS.value, Permission.WRITE_CLIENTS.value,
            Permission.READ_OWN.value, Permission.WRITE_OWN.value
        ]
    },
    "staff": {
        "name": "スタッフ",
        "description": "一般スタッフ。基本的な操作権限を持つ。",
        "permissions": [
            Permission.READ_LOCATIONS.value,
            Permission.READ_CATALOG.value,
            Permission.READ_INVENTORY.value,
            Permission.READ_SCHEDULES.value, Permission.WRITE_SCHEDULES.value,
            Permission.READ_CLIENTS.value, Permission.WRITE_CLIENTS.value,
            Permission.READ_OWN.value, Permission.WRITE_OWN.value
        ]
    }
}

def get_user_permissions(user: User) -> List[str]:
    """ユーザーの権限リストを取得"""
    # スーパーユーザーは全権限を持つ
    if user.is_superuser:
        return [p.value for p in Permission]
    
    # ロールがない場合は基本権限のみ
    if not user.role or not user.role.permissions:
        return [Permission.READ_OWN.value, Permission.WRITE_OWN.value]
    
    # JSON文字列から権限リストに変換
    import json
    try:
        return json.loads(user.role.permissions)
    except json.JSONDecodeError:
        return [Permission.READ_OWN.value, Permission.WRITE_OWN.value]

def has_permission(required_permission: Permission):
    """権限チェック用の依存関係"""
    def dependency(current_user: User = Depends(get_current_active_user)):
        # ユーザーの権限を取得
        user_permissions = get_user_permissions(current_user)
        
        # スーパーユーザーまたは管理者権限を持つ場合は許可
        if current_user.is_superuser or Permission.ADMIN.value in user_permissions:
            return current_user
            
        # 必要な権限を持っているか確認
        if required_permission.value not in user_permissions:
            raise ForbiddenException(detail=f"Required permission: {required_permission.value}")
            
        return current_user
    return dependency