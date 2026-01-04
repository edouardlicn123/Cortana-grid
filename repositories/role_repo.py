# repositories/role_repo.py
# 角色权限数据访问层：角色列表、权限读写

from .base import get_db_connection
from utils import logger

def get_all_roles():
    """获取所有角色列表（用于角色管理页面）"""
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT id, name, description FROM role ORDER BY id"
            ).fetchall()
        return [dict(row) for row in rows]

    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        return []


def get_role_permissions(role_id: int):
    """获取指定角色的权限列表"""
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                "SELECT permission FROM role_permission WHERE role_id = ?",
                (role_id,)
            ).fetchall()
        return [row['permission'] for row in rows]

    except Exception as e:
        logger.error(f"获取角色权限失败 (role_id={role_id}): {e}")
        return []


def save_role_permissions(role_id: int, permissions: list[str]):
    """保存角色权限（先删除旧的，再插入新的）"""
    try:
        with get_db_connection() as conn:
            # 删除旧权限
            conn.execute(
                "DELETE FROM role_permission WHERE role_id = ?",
                (role_id,)
            )

            # 插入新权限
            if permissions:
                conn.executemany(
                    "INSERT INTO role_permission (role_id, permission) VALUES (?, ?)",
                    [(role_id, perm) for perm in permissions]
                )

            conn.commit()
        return True

    except Exception as e:
        logger.error(f"保存角色权限失败 (role_id={role_id}): {e}")
        return False
