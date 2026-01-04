# models.py
# 用户模型（Flask-Login 兼容 + 支持 current_user.username + 权限检查）

from flask_login import UserMixin

class User(UserMixin, dict):
    """
    用户模型：继承 UserMixin 和 dict
    支持 current_user.username, current_user.display_name, current_user.has_permission()
    """

    def __init__(self, user_dict):
        super().__init__(user_dict)
        self.id = user_dict.get('id')

    # Flask-Login 所需方法
    def is_authenticated(self):
        return True

    def is_active(self):
        return self.get('is_active', True)

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    # ==================== 常用属性 ====================
    @property
    def username(self):
        """支持 current_user.username"""
        return self.get('username')

    @property
    def display_name(self):
        """导航栏显示名称：优先 full_name，其次 username"""
        return self.get('full_name') or self.get('username') or '未知用户'

    # ==================== 权限检查 ====================
    def has_permission(self, permission):
        """检查是否拥有指定权限"""
        if self.get('is_admin'):
            return True

        user_permissions = self.get('permissions', '')
        if not user_permissions:
            return False

        required_perm = permission.strip()
        for p in user_permissions.split(';'):
            p = p.strip()
            if not p:
                continue
            if p == required_perm:
                return True
            if p.endswith('*'):
                prefix = p[:-1]
                if required_perm.startswith(prefix):
                    return True
        return False

    def __repr__(self):
        return f'<User id={self.id} username={self.username} is_admin={self.get("is_admin")}>'
