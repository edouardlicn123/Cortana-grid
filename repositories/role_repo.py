# repositories/role_repo.py
# 角色权限数据访问层（优化终极版 - 功能完全不变，代码更健壮、可读、专业）

from .base import get_db_connection
from utils import logger
from typing import List, Dict, Optional, Tuple, Any


def get_all_roles() -> List[Dict]:
    """
    获取所有角色列表（用于系统设置中的角色权限管理页面）

    Returns:
        List[Dict]: 包含 id, name, description 的角色字典列表
    """
    query = "SELECT id, name, description FROM role ORDER BY id"

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query).fetchall()

        roles = [dict(row) for row in rows]

        logger.info(f"成功加载角色列表：共 {len(roles)} 个角色")
        return roles

    except Exception as e:
        logger.error(f"获取角色列表失败: {e}")
        return []


def get_role_permissions(role_id: int) -> List[str]:
    """
    获取指定角色的所有权限标识列表

    Args:
        role_id: 角色 ID

    Returns:
        List[str]: 该角色拥有的权限字符串列表
    """
    query = "SELECT permission FROM role_permission WHERE role_id = ?"

    try:
        with get_db_connection() as conn:
            rows = conn.execute(query, (role_id,)).fetchall()

        permissions = [row['permission'] for row in rows]

        logger.debug(f"加载角色权限成功 (role_id={role_id}): {len(permissions)} 项")
        return permissions

    except Exception as e:
        logger.error(f"获取角色权限失败 (role_id={role_id}): {e}")
        return []


def save_role_permissions(role_id: int, permissions: List[str]) -> bool:
    """
    保存（覆盖）指定角色的权限配置

    操作流程：
    1. 删除该角色所有现有权限
    2. 批量插入新的权限列表

    Args:
        role_id: 角色 ID
        permissions: 要赋予的新权限列表（字符串）

    Returns:
        bool: 保存是否成功
    """
    try:
        with get_db_connection() as conn:
            # Step 1: 删除旧权限
            conn.execute(
                "DELETE FROM role_permission WHERE role_id = ?",
                (role_id,)
            )

            # Step 2: 插入新权限（如果有）
            if permissions:
                placeholder_data = [(role_id, perm.strip()) for perm in permissions if perm.strip()]
                conn.executemany(
                    "INSERT INTO role_permission (role_id, permission) VALUES (?, ?)",
                    placeholder_data
                )

            conn.commit()

        logger.info(f"角色权限保存成功 (role_id={role_id}): {len(permissions)} 项权限")
        return True

    except Exception as e:
        logger.error(f"保存角色权限失败 (role_id={role_id}): {e}")
        conn.rollback() if 'conn' in locals() else None
        return False
