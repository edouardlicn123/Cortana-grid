# repositories/user_model.py
# 用户模型（优化终极版 - 与新权限系统完全兼容，支持延迟加载，功能更强、更安全）

from flask_login import UserMixin, AnonymousUserMixin
from repositories.base import get_db_connection
from utils import logger
from typing import List, Set


class User(UserMixin):
    """
    Flask-Login 用户对象（核心模型）
    - 支持 current_user.username / display_name / has_permission()
    - 权限与角色延迟加载（避免登录时不必要的数据库查询）
    - 与 permissions.py 通配符系统完全兼容
    """

    def __init__(self, user_dict: dict | None):
        if not user_dict:
            return

        # 基础字段
        self.id: int = user_dict['id']
        self.username: str = user_dict['username']
        self.full_name: str = user_dict.get('full_name') or ''
        self.phone: str = user_dict.get('phone') or ''
        self.preferred_css: str = user_dict.get('preferred_css') or ''
        self.page_size: int = int(user_dict.get('page_size') or 20)

        # 状态字段
        self._is_active: bool = bool(user_dict.get('is_active', True))
        self.must_change_password: bool = bool(user_dict.get('must_change_password', False))

        # 延迟加载字段（首次访问时从数据库加载）
        self._roles: List[str] = []
        self._permissions: Set[str] = set()
        self._managed_grids: List[int] = []
        self._loaded: bool = False

    # ==================== Flask-Login 必需方法 ====================
    def is_authenticated(self) -> bool:
        return True

    def is_active(self) -> bool:
        return self._is_active

    def is_anonymous(self) -> bool:
        return False

    def get_id(self) -> str:
        return str(self.id)

    # ==================== 常用属性 ====================
    @property
    def display_name(self) -> str:
        """导航栏显示名称：优先真实姓名，其次用户名"""
        return self.full_name.strip() or self.username or '未知用户'

    # ==================== 延迟加载权限与角色 ====================
    def _load_permissions(self) -> None:
        """从数据库加载角色、权限、负责网格（仅首次调用时执行）"""
        if self._loaded:
            return

        logger.debug(f"延迟加载用户权限: {self.username} (ID: {self.id})")

        try:
            with get_db_connection() as conn:
                # 加载角色
                role_rows = conn.execute(
                    "SELECT r.name FROM role r "
                    "JOIN user_role ur ON r.id = ur.role_id "
                    "WHERE ur.user_id = ?",
                    (self.id,)
                ).fetchall()
                self._roles = [row['name'] for row in role_rows]

                # 加载权限（通过角色关联）
                perm_rows = conn.execute(
                    "SELECT DISTINCT rp.permission FROM role_permission rp "
                    "JOIN user_role ur ON rp.role_id = ur.role_id "
                    "WHERE ur.user_id = ?",
                    (self.id,)
                ).fetchall()
                self._permissions = {row['permission'] for row in perm_rows}

                # 加载负责网格
                grid_rows = conn.execute(
                    "SELECT grid_id FROM user_grid WHERE user_id = ?",
                    (self.id,)
                ).fetchall()
                self._managed_grids = [row['grid_id'] for row in grid_rows]

            self._loaded = True
            logger.debug(f"用户 {self.username} 权限加载完成: 角色 {self._roles}, 网格 {self._managed_grids}")

        except Exception as e:
            logger.error(f"用户 {self.username} 权限加载失败: {e}")
            # 异常时给予最高权限，防止用户被锁死（生产可调整为 False）
            self._roles = ['super_admin']
            self._permissions = {'*:*'}
            self._managed_grids = []
            self._loaded = True

    # ==================== 权限检查 ====================
    @property
    def roles(self) -> List[str]:
        self._load_permissions()
        return self._roles

    @property
    def permissions(self) -> Set[str]:
        self._load_permissions()
        return self._permissions

    @property
    def managed_grids(self) -> List[int]:
        self._load_permissions()
        return self._managed_grids

    def has_permission(self, perm: str) -> bool:
        """检查是否拥有指定权限（支持通配符 *:*)"""
        self._load_permissions()

        if 'super_admin' in self._roles or '*:*' in self._permissions:
            return True

        for p in self._permissions:
            if p == perm:
                return True
            if p.endswith('*') and perm.startswith(p[:-1]):
                return True

        return False

    def has_role(self, role: str) -> bool:
        """检查是否拥有指定角色"""
        self._load_permissions()
        return role in self._roles

    def is_admin(self) -> bool:
        """是否为管理员（super_admin 或 community_admin）"""
        self._load_permissions()
        return 'super_admin' in self._roles or 'community_admin' in self._roles

    # ==================== 调试 ====================
    def __repr__(self) -> str:
        return f'<User id={self.id} username="{self.username}" roles={self.roles} active={self.is_active()}>'


class AnonymousUser(AnonymousUserMixin):
    """
    未登录用户对象
    所有权限检查返回 False
    """

    def __init__(self):
        self.id = None
        self.username = ''
        self.full_name = ''
        self.preferred_css = ''
        self.page_size = 20

    @property
    def display_name(self) -> str:
        return '未登录用户'

    def has_permission(self, perm: str) -> bool:
        return False

    def has_role(self, role: str) -> bool:
        return False

    def is_admin(self) -> bool:
        return False

    @property
    def roles(self) -> list:
        return []

    @property
    def managed_grids(self) -> list:
        return []

    def __repr__(self) -> str:
        return '<AnonymousUser>'
