# routes/main.py
# 文件功能说明：
#   - 定义主页面蓝图 (main_bp)，负责系统首页（概览页面）的路由处理
#   - 唯一路由：GET /（登录后重定向至 /overview）
#   - 核心职责：
#       • 获取社区基础统计数据（总人数、重点人员、建筑数、网格数）
#       • 为前端 ECharts 仪表盘准备结构化图表数据：
#           - 人员类型分布（饼图/环形图）
#           - 各网格人员数量（柱状图）
#           - 建筑类型分布（环形图）
#       • 统一异常处理：数据获取失败时返回安全默认值，确保页面不崩溃
#       • 详细日志记录，便于生产环境监控和排查
#   - 依赖：repositories.person_repo 和 repositories.building_repo 中的统计查询函数
#   - 模板：render_template('overview.html', stats=..., chart_data=...)
#   - 版本：v2.3（仪表盘增强版）

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from repositories.person_repo import (
    get_overview_stats,
    get_person_count_by_type,
    get_person_count_by_grid
)
from repositories.building_repo import get_building_count_by_type
from utils import logger


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@login_required
def overview():
    """社区概览首页（含动态统计仪表盘数据）"""
    username = current_user.username if current_user.is_authenticated else '未知用户'

    # 初始化默认值（防止异常时页面崩溃）
    stats = {
        'total_persons': 0,
        'key_persons': 0,
        'total_buildings': 0,
        'total_grids': 0,
    }

    # 图表数据默认值
    chart_data = {
        'person_type': [],      # 人员类型分布（饼图）
        'grid_person': {'names': [], 'counts': []},  # 各网格人员数量（柱状图）
        'building_type': [],    # 建筑类型分布（环形图）
    }

    try:
        # 1. 基础统计数据
        stats = get_overview_stats()

        # 2. 人员类型分布（饼图/环形图所需格式：[{name: ..., value: ...}, ...]）
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

        logger.info(f"用户 {username} 查看社区概览成功: 基础统计 {stats} | 图表数据已准备（人员类型 {len(chart_data['person_type'])} 项，网格 {len(chart_data['grid_person']['names'])} 个，建筑类型 {len(chart_data['building_type'])} 项）")

    except Exception as e:
        logger.error(f"用户 {username} 获取社区概览数据失败: {type(e).__name__}: {e}")
        logger.warning(f"用户 {username} 查看社区概览（使用默认空数据）: 基础统计 {stats} | 图表数据为空")

    return render_template(
        'overview.html',
        stats=stats,
        chart_data=chart_data
    )
