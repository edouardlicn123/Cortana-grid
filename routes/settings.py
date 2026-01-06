# routes/settings.py
# 个人设置路由（优化版 - 代码更简洁、可读性提升、健壮性更强，功能完全不变）

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from repositories.base import get_db_connection
from utils import logger


settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/personal_settings', methods=['GET', 'POST'])
@login_required
def personal_settings():
    """个人设置页面（显示姓名、分页大小、主题切换）"""

    # ==================== 加载可用主题列表 ====================
    themes_dir = os.path.join(current_app.static_folder, 'themes')
    available_themes = ['']  # 空字符串代表默认主题

    if os.path.isdir(themes_dir):
        try:
            theme_files = sorted([
                f for f in os.listdir(themes_dir)
                if f.lower().endswith('.css') and os.path.isfile(os.path.join(themes_dir, f))
            ])
            available_themes.extend([f'themes/{f}' for f in theme_files])
        except Exception as e:
            logger.warning(f"扫描主题目录失败: {e}")

    # ==================== POST 处理保存 ====================
    if request.method == 'POST':
        updates = {}

        try:
            # 1. 显示姓名
            full_name = request.form.get('full_name', '').strip()
            current_full_name = current_user.full_name or ''
            if full_name != current_full_name:
                updates['full_name'] = full_name if full_name else None

            # 2. 每页条数
            page_size_str = request.form.get('page_size', '').strip()
            if page_size_str.isdigit():
                page_size = int(page_size_str)
                if 10 <= page_size <= 100:
                    if page_size != current_user.page_size:
                        updates['page_size'] = page_size
                else:
                    flash('每页条数必须在 10-100 之间，已忽略此修改', 'warning')
            elif page_size_str:
                flash('每页条数格式不正确，已忽略此修改', 'warning')

            # 3. 界面主题（只保存纯文件名 xxx.css）
            preferred_css_form = request.form.get('preferred_css', '').strip()
            current_theme = current_user.preferred_css or ''

            if preferred_css_form:
                if f'themes/{preferred_css_form}' in available_themes:
                    new_theme = preferred_css_form
                else:
                    flash('所选主题无效，已忽略此修改', 'warning')
                    new_theme = current_theme
            else:
                new_theme = ''

            if new_theme != current_theme:
                updates['preferred_css'] = new_theme

            # ==================== 数据库更新 ====================
            if updates:
                with get_db_connection() as conn:
                    set_clause = ', '.join(f"{k} = ?" for k in updates)
                    values = list(updates.values()) + [current_user.id]
                    conn.execute(f"UPDATE user SET {set_clause} WHERE id = ?", values)
                    conn.commit()

                # 更新当前用户对象（立即生效）
                for key, value in updates.items():
                    setattr(current_user, key, value)

                flash('个人设置保存成功！', 'success')
            else:
                flash('没有检测到任何修改', 'info')

        except Exception as e:
            logger.error(f"用户 {current_user.id} 保存个人设置失败: {e}")
            flash('保存失败，请重试', 'error')

        return redirect(url_for('settings.personal_settings'))

    # ==================== GET 渲染页面 ====================
    return render_template(
        'settings.html',
        available_themes=available_themes
    )
