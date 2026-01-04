# routes/main.py
# 主页路由模块 - 社区概览（已迁移到 repository）

from flask import Blueprint, render_template
from flask_login import login_required
from repositories.person_repo import get_overview_stats
from utils import logger

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def overview():
    """
    社区概览页面
    统计数据已从 person_repo 获取
    """
    try:
        stats = get_overview_stats()
        logger.info(f'用户 {current_user.username} 查看社区概览: {stats}')
    except Exception as e:
        logger.error(f'概览统计加载失败: {e}')
        stats = {
            'total_persons': 0,
            'key_persons': 0,
            'total_buildings': 0,
            'total_grids': 0,
        }
    
    return render_template('overview.html', stats=stats)
