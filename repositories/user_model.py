# repositories/user_model.py
# 用户对象定义（优化终极版 - 功能完全不变，代码更健壮、可读、专业）

from flask_login import UserMixin, AnonymousUserMixin
from repositories.base import get_db_connection
from utils import logger
from typing import Set, List, Dict, Optional, Tuple, Any


class User(UserMixin):
    """
    Flask-Login 用户对象
    - 支持延迟加载角色、权限、负责网格
    - 提供 has_permission / has_role / is_admin 等便捷方法
    - 权限支持通配符（如 resource:building:*）
    """

    def __init__(self, user_dict: dict | None):
        if not user_dict:
            return

        self.id: int = user_dict['id']
        self.username: str = user_dict['username']
        self.password_hash: str | None = user_dict.get('password_hash')
        self.preferred_css: str = user_dict.get('preferred_css') or ''
        self.full_name: str = user_dict.get('full_name') or ''
        self.phone: str = user_dict.get('phone') or ''
        self.page_size: int = int(user_dict.get('page_size') or 20)

        self._db_is_active: bool = bool(user_dict.get('is_active', True))
        self.must_change_password: bool = bool(user_dict.get('must_change_password', False))

        # 延迟加载属性
        self.roles: List[str] = []
        self.permissions: Set[str] = set()
        self.managed_grids: List[int] = []

        self._permissions_loaded: bool = False

    def load_permissions(self) -> None:
        """延迟加载用户角色、权限和负责网格"""
        if self._permissions_loaded:
            return

        logger.debug(f"开始加载用户权限信息: {self.username} (ID: {self.id})")

        try:
            with get_db_connection() as conn:
                # 1. 加载角色
                roles_rows = conn.execute(
                    """
                    SELECT r.name 
                    FROM role r
                    JOIN user_role ur ON r.id = ur.role_id
                    WHERE ur.user_id = ?
                    """,
                    (self.id,)
                ).fetchall()

                self.roles = [row['name'] for row in roles_rows]
                logger.debug(f"用户角色加载完成: {self.roles}")

                # 2. 加载权限（优先从数据库）
                perms_rows = conn.execute(
                    """
                    SELECT DISTINCT rp.permission 
                    FROM role_permission rp
                    JOIN user_role ur ON rp.role_id = ur.role_id
                    WHERE ur.user_id = ?
                    """,
                    (self.id,)
                ).fetchall()

                db_permissions = {row['permission'] for row in perms_rows}
                logger.debug(f"数据库权限加载: {db_permissions}")

                final_permissions = db_permissions

                # 3. 若数据库无配置，回退到硬编码默认权限
                if not db_permissions:
                    try:
                        from permissions import DEFAULT_ROLE_PERMISSIONS
                        for role in self.roles:
                            final_permissions.update(DEFAULT_ROLE_PERMISSIONS.get(role, set()))
                        logger.debug(f"使用硬编码默认权限: {final_permissions}")
                    except ImportError:
                        logger.warning("permissions.py 未找到，无法加载默认权限")

                self.permissions = final_permissions

                # 4. 加载负责网格
                grids_rows = conn.execute(
                    """
                    SELECT g.id 
                    FROM grid g
                    JOIN user_grid ug ON g.id = ug.grid_id
                    WHERE ug.user_id = ?
                    """,
                    (self.id,)
                ).fetchall()

                self.managed_grids = [row['id'] for row in grids_rows]
                logger.debug(f"负责网格加载完成: {self.managed_grids}")

            self._permissions_loaded = True
            logger.debug(f"用户 {self.username} 权限加载成功")

        except Exception as e:
            logger.error(f"用户 {self.username} (ID: {self.id}) 权限加载失败: {e}")
            # 保险策略：异常时给予最高权限，防止用户被锁死
            self.roles = ['super_admin']
            self.permissions = {'*:*'}
            self.managed_grids = []
            self._permissions_loaded = True

    @property
    def is_active(self) -> bool:
        """Flask-Login 要求：账户是否启用"""
        return self._db_is_active

    @property
    def display_name(self) -> str:
        """前端显示名称：优先使用真实姓名"""
        return self.full_name.strip() or self.username

    def has_permission(self, perm: str) -> bool:
        """
        检查是否拥有指定权限（支持通配符 *）

        示例：
            resource:building:view → 精确匹配
            resource:building:*   → 匹配所有 building 操作
            *:*                   → 所有权限
        """
        self.load_permissions()

        if 'super_admin' in self.roles or '*:*' in self.permissions:
            return True

        for p in self.permissions:
            if p == perm:
                return True
            if p.endswith('*') and perm.startswith(p[:-1]):
                return True

        return False

    def has_role(self, role: str) -> bool:
        """检查是否拥有指定角色"""
        self.load_permissions()
        return role in self.roles

    def is_admin(self) -> bool:
        """是否为管理员（超级管理员 或 社区管理员）"""
        self.load_permissions()
        return 'super_admin' in self.roles or 'community_admin' in self.roles


class AnonymousUser(AnonymousUserMixin):
    """
    未登录用户对象（Flask-Login 要求）
    所有权限检查返回 False
    """

    def has_permission(self, perm: str) -> bool:
        return False

    def has_role(self, role: str) -> bool:
        return False

    def is_admin(self) -> bool:
        return False

    @property
    def display_name(self) -> str:
        return "未登录用户"

    # 兼容属性（避免模板报错）
    id: Any = None
    username: str = ''
    preferred_css: str = ''
    full_name: str = ''
    phone: str = ''
    page_size: int = 20
    managed_grids: List[int] = []
    roles: List[str] = []
    permissions: Set[str] = set()
