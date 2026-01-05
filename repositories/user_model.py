# repositories/user_model.py
# 用户对象定义（添加权限加载日志 + 更健壮处理）

from flask_login import UserMixin, AnonymousUserMixin
from repositories.base import get_db_connection
from utils import logger

class User(UserMixin):
    def __init__(self, user_dict):
        if not user_dict:
            return

        self.id = user_dict['id']
        self.username = user_dict['username']
        self.password_hash = user_dict.get('password_hash')
        self.preferred_css = user_dict.get('preferred_css') or ''
        self.full_name = user_dict.get('full_name') or ''
        self.phone = user_dict.get('phone') or ''
        self.page_size = user_dict.get('page_size') or 20

        self._db_is_active = bool(user_dict.get('is_active', True))
        self.must_change_password = bool(user_dict.get('must_change_password', False))

        # 延迟加载
        self.roles = []
        self.permissions = set()
        self.managed_grids = []

    def load_permissions(self):
        if hasattr(self, '_permissions_loaded') and self._permissions_loaded:
            return

        logger.debug(f"开始加载用户 {self.username} (ID: {self.id}) 的权限和角色...")

        try:
            with get_db_connection() as conn:
                # 加载角色
                roles_rows = conn.execute('''
                    SELECT r.name FROM role r
                    JOIN user_role ur ON r.id = ur.role_id
                    WHERE ur.user_id = ?
                ''', (self.id,)).fetchall()
                self.roles = [row['name'] for row in roles_rows]
                logger.debug(f"加载到角色: {self.roles}")

                # 加载权限（数据库配置优先）
                perms_rows = conn.execute('''
                    SELECT rp.permission FROM role_permission rp
                    JOIN user_role ur ON rp.role_id = ur.role_id
                    WHERE ur.user_id = ?
                ''', (self.id,)).fetchall()
                db_permissions = {row['permission'] for row in perms_rows}
                logger.debug(f"从数据库加载权限: {db_permissions}")

                # 如果数据库无权限配置，回退到硬编码默认
                final_permissions = db_permissions
                if not db_permissions:
                    from permissions import DEFAULT_ROLE_PERMISSIONS
                    for role in self.roles:
                        final_permissions.update(DEFAULT_ROLE_PERMISSIONS.get(role, []))
                    logger.debug(f"使用硬编码默认权限: {final_permissions}")

                self.permissions = final_permissions

                # 加载负责网格
                grids_rows = conn.execute('''
                    SELECT g.id FROM grid g
                    JOIN user_grid ug ON g.id = ug.grid_id
                    WHERE ug.user_id = ?
                ''', (self.id,)).fetchall()
                self.managed_grids = [row['id'] for row in grids_rows]
                logger.debug(f"加载负责网格: {self.managed_grids}")

            self._permissions_loaded = True
            logger.debug(f"用户 {self.username} 权限加载完成")
        except Exception as e:
            logger.error(f"用户 {self.username} 权限加载异常: {e}")
            self.roles = ['super_admin']  # 保险：强制给 super_admin 权限
            self.permissions = {'*:*'}
            self.managed_grids = []
            self._permissions_loaded = True

    @property
    def is_active(self):
        return self._db_is_active

    @property
    def display_name(self):
        return self.full_name.strip() or self.username

    def has_permission(self, perm: str) -> bool:
        self.load_permissions()
        if 'super_admin' in self.roles or '*:*' in self.permissions:
            return True
        for p in self.permissions:
            if p == perm or (p.endswith('*') and perm.startswith(p[:-1])):
                return True
        return False

    def has_role(self, role: str) -> bool:
        self.load_permissions()
        return role in self.roles

    def is_admin(self):
        self.load_permissions()
        return 'super_admin' in self.roles or 'community_admin' in self.roles


class AnonymousUser(AnonymousUserMixin):
    def has_permission(self, perm: str) -> bool:
        return False

    def has_role(self, role: str) -> bool:
        return False

    @property
    def display_name(self):
        return "未登录"

    @property
    def is_admin(self):
        return False

    preferred_css = ''
    full_name = ''
    page_size = 20
    managed_grids = []
    roles = []
