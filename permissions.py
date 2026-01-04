# permissions.py
# 权限管理系统核心模块（支持通配符 + 网格隔离）

from flask import abort, request
from flask_login import current_user
from functools import wraps
from repositories.base import get_db_connection
from utils import logger

# ==================== 资源与操作定义 ====================
RESOURCES = {
    'person': '人员',
    'building': '小区/建筑',
    'grid': '网格',
}

ACTIONS = ['view', 'edit', 'delete']

SPECIAL_PERMISSIONS = {
    'import_export:all': '导入导出功能完整权限',
    'system:view': '访问系统设置页面',
    'system:manage_permissions': '管理角色权限（仅 super_admin）',
}

# ==================== 角色默认权限兜底 ====================
DEFAULT_ROLE_PERMISSIONS = {
    'super_admin': ['*:*'],
    'community_admin': [
        'resource:person:*', 'resource:building:*', 'resource:grid:*',
        'import_export:all', 'system:view',
    ],
    'grid_user': [
        'resource:person:view', 'resource:person:edit', 'resource:person:delete',
        'resource:building:view', 'resource:grid:view',
    ],
}

# ==================== 数据库权限查询 ====================
def get_role_permissions(role_name):
    with get_db_connection() as conn:
        role_row = conn.execute('SELECT id FROM role WHERE name = ?', (role_name,)).fetchone()
        if role_row:
            rows = conn.execute(
                'SELECT permission FROM role_permission WHERE role_id = ?',
                (role_row['id'],)
            ).fetchall()
            perms = [row['permission'] for row in rows]
            if perms:
                return perms
    return DEFAULT_ROLE_PERMISSIONS.get(role_name, [])

# ==================== 权限检查核心 ====================
def has_permission(required_perm: str) -> bool:
    if not current_user.is_authenticated:
        return False

    user_perms = set()
    for role in current_user.roles:
        user_perms.update(get_role_permissions(role))

    if '*:*' in user_perms:
        return True
    resource_part = required_perm.rsplit(':', 1)[0]
    if f'{resource_part}:*' in user_perms:
        return True
    if required_perm in user_perms:
        return True

    return False

# ==================== 装饰器 ====================
def permission_required(required_perm):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not has_permission(required_perm):
                logger.warning(f"权限拒绝: {current_user.username if current_user.is_authenticated else '未登录'} 无权访问 {required_perm}")
                abort(403)
            return f(*args, **kwargs)
        return decorated
    return decorator

# ==================== 网格数据隔离 ====================
def grid_data_permission(write=False):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)

            if 'super_admin' in current_user.roles or 'community_admin' in current_user.roles:
                return f(*args, **kwargs)

            if 'grid_user' not in current_user.roles or not current_user.managed_grids:
                abort(403)

            building_id = None
            if 'bid' in kwargs:
                building_id = kwargs['bid']
            elif request.form.get('living_building_id'):
                building_id = request.form.get('living_building_id')
            elif request.form.get('household_building_id'):
                building_id = request.form.get('household_building_id')
            elif 'pid' in kwargs:
                pid = kwargs['pid']
                with get_db_connection() as conn:
                    row = conn.execute('SELECT living_building_id FROM person WHERE id = ?', (pid,)).fetchone()
                    if row:
                        building_id = row['living_building_id']

            if building_id:
                try:
                    building_id = int(building_id)
                    with get_db_connection() as conn:
                        grid_row = conn.execute('SELECT grid_id FROM building WHERE id = ?', (building_id,)).fetchone()
                        if grid_row and grid_row['grid_id'] not in current_user.managed_grids:
                            abort(403, "您无权操作非负责网格下的数据")
                except:
                    pass

            if write and not has_permission('resource:person:edit'):
                abort(403)

            return f(*args, **kwargs)
        return decorated
    return decorator

# ==================== 导入导出逐行检查 ====================
def check_user_grid_permission(building_id: int) -> bool:
    if not current_user.is_authenticated:
        return False
    if 'super_admin' in current_user.roles or 'community_admin' in current_user.roles:
        return True
    if 'grid_user' not in current_user.roles or not current_user.managed_grids:
        return False

    try:
        with get_db_connection() as conn:
            row = conn.execute(
                'SELECT grid_id FROM building WHERE id = ? AND is_deleted = 0',
                (building_id,)
            ).fetchone()
            if row and row['grid_id'] in current_user.managed_grids:
                return True
    except Exception as e:
        logger.error(f"网格权限检查失败: {e}")
    return False
