# routes/main.py
# 主页面蓝图 - 负责首页概览（仪表盘）
# 版本：v2.3（仪表盘增强版）

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime

from repositories.person_repo import (
    get_overview_stats,
    get_person_count_by_type,
    get_person_count_by_grid
)
from repositories.building_repo import get_building_count_by_type
from repositories.grid_repo import get_all_grids  # 如果你有这个函数
from utils import logger

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def index():
    """登录后默认跳转到概览页"""
    return redirect(url_for('main.overview'))


@main_bp.route('/overview')
@login_required
def overview():
    """社区概览首页 - 仪表盘页面"""
    username = current_user.username if current_user.is_authenticated else '未知用户'

    # 初始化默认值，防止异常时页面崩溃
    stats = {
        'total_persons': 0,
        'key_persons': 0,
        'total_buildings': 0,
        'total_grids': 0,
    }

    # 图表数据默认值
    chart_data = {
        'person_type': [],           # 人员类型分布（饼图）
        'grid_person': {'names': [], 'counts': []},  # 各网格人员数量（柱状图）
        'building_type': [],         # 建筑类型分布（环形图）
    }

    try:
        # 1. 基础统计数据
        stats = get_overview_stats()

        # 2. 人员类型分布（饼图所需格式）
        person_type_rows = get_person_count_by_type()
        chart_data['person_type'] = [
            {'name': row['person_type'] or '未分类', 'value': row['count']}
            for row in person_type_rows
        ]

        # 3. 各网格人员数量（柱状图）
        grid_rows = get_person_count_by_grid()
        chart_data['grid_person'] = {
            'names': [row['grid_name'] or '无网格' for row in grid_rows],
            'counts': [row['count'] for row in grid_rows]
        }

        # 4. 建筑类型分布（环形图）
        building_type_rows = get_building_count_by_type()
        chart_data['building_type'] = [
            {'name': row['type_display'], 'value': row['count']}
            for row in building_type_rows
        ]

        logger.info(
            f"用户 {username} 查看社区概览成功: "
            f"基础统计 {stats} | "
            f"图表数据准备完成（人员类型 {len(chart_data['person_type'])} 项，"
            f"网格 {len(chart_data['grid_person']['names'])} 个，"
            f"建筑类型 {len(chart_data['building_type'])} 项）"
        )

    except Exception as e:
        logger.error(f"用户 {username} 获取社区概览数据失败: {type(e).__name__}: {e}")
        logger.warning(f"用户 {username} 使用默认空数据展示概览页")

    # 渲染模板并传递数据
    return render_template(
        'overview.html',
        stats=stats,
        chart_data=chart_data,
        current_year=datetime.now().year,
        community_name=current_user.community_name if hasattr(current_user, 'community_name') else '社区'
    )


# 可选：添加一个简单的健康检查路由（调试用）
@main_bp.route('/health')
def health():
    return {"status": "healthy", "message": "Main blueprint is working"}, 200
