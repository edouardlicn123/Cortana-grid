# routes/main.py（必须是这个版本）
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from repositories.person_repo import get_overview_stats
from utils import logger

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def overview():
    try:
        stats = get_overview_stats()
        username = current_user.username if current_user.is_authenticated else '未知用户'
        logger.warning(f'用户 {username} 查看社区概览: {stats}')
    except Exception as e:
        logger.error(f'获取概览统计失败: {type(e).__name__}: {e}')  # ← 关键：打印异常类型和信息
        stats = {
            'total_persons': 0,
            'key_persons': 0,
            'total_buildings': 0,
            'total_grids': 0,
        }
        username = current_user.username if current_user.is_authenticated else '未知用户'
        logger.warning(f'用户 {username} 查看社区概览（统计失败，使用默认值）: {stats}')
    
    return render_template('overview.html', stats=stats)
