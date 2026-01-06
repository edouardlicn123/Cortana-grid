# services/settings_service.py
# 系统全局设置业务逻辑（优化版 - 轻量、可扩展、健壮）

from repositories.settings_repo import get_setting, set_setting
from flask_login import current_user
from utils import logger


def get_community_name(default: str = '阳光社区') -> str:
    """获取当前社区名称（带默认值兜底）"""
    return get_setting('community_name', default)


def update_community_name(new_name: str) -> tuple[bool, str]:
    """更新社区名称"""
    try:
        new_name = new_name.strip()

        if not new_name:
            return False, '社区名称不能为空'

        if len(new_name) > 100:
            return False, '社区名称不能超过100个字符'

        set_setting('community_name', new_name)

        logger.info(f"用户 {current_user.username} 将社区名称修改为: {new_name}")
        return True, '社区名称更新成功'

    except Exception as e:
        logger.error(f"用户 {current_user.username} 更新社区名称失败: {e}")
        return False, '更新失败，请重试'
