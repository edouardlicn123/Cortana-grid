# routes/main.py
# 主页路由（优化版 - 代码更简洁、可读性提升、日志更清晰，功能完全不变）

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from repositories.person_repo import get_overview_stats
from utils import logger


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def overview():
    """社区概览首页"""
    username = current_user.username if current_user.is_authenticated else '未知用户'

    try:
        stats = get_overview_stats()
        logger.info(f"用户 {username} 查看社区概览: {stats}")
    except Exception as e:
        logger.error(f"用户 {username} 获取社区概览统计失败: {type(e).__name__}: {e}")
        stats = {
            'total_persons': 0,
            'key_persons': 0,
            'total_buildings': 0,
            'total_grids': 0,
        }
        logger.warning(f"用户 {username} 查看社区概览（使用默认统计值）: {stats}")

    return render_template('overview.html', stats=stats)
