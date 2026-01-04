# routes/settings.py
# 个人设置路由 - 最终完美稳定版
# 特性：
# - 主题列表完整显示（所有 static/themes/*.css）
# - 主题保存真正生效（数据库存纯文件名 xxx.css，与项目原始机制完全一致）
# - 保存提示准确（成功/无修改/非法输入警告）
# - 兼容旧数据（旧记录可能是 '' 或 'dark.css'）
# - 字段校验宽容健壮

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from repositories.base import get_db_connection
from utils import logger
import os
from flask import current_app

settings_bp = Blueprint('settings', __name__, url_prefix='/settings')

@settings_bp.route('/personal_settings', methods=['GET', 'POST'])
@login_required
def personal_settings():
    # ==================== 生成可用主题列表（完整路径格式，用于模板显示） ====================
    available_themes = ['']  # 空字符串 = 默认主题
    themes_dir = os.path.join(current_app.static_folder, 'themes')
    if os.path.isdir(themes_dir):
        try:
            theme_files = [
                f for f in os.listdir(themes_dir)
                if f.lower().endswith('.css') and os.path.isfile(os.path.join(themes_dir, f))
            ]
            # 生成完整路径，用于模板中 selected 判断和显示
            available_themes.extend([f'themes/{f}' for f in sorted(theme_files)])
        except Exception as e:
            logger.warning(f"扫描主题目录失败: {e}")

    # ==================== POST 保存逻辑 ====================
    if request.method == 'POST':
        try:
            updates = {}

            # 1. 显示姓名
            full_name = request.form.get('full_name', '').strip()
            if full_name != (current_user.full_name or ''):
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

            # 3. 界面主题（关键：只保存纯文件名 xxx.css）
            preferred_css_form = request.form.get('preferred_css', '').strip()  # 前端传纯文件名
            if preferred_css_form:
                # 校验是否合法（检查 themes/preferred_css_form 是否存在）
                if f'themes/{preferred_css_form}' in available_themes:
                    preferred_css_new = preferred_css_form
                else:
                    flash('所选主题无效，已忽略此修改', 'warning')
                    preferred_css_new = current_user.preferred_css or ''
            else:
                preferred_css_new = ''

            # 判断是否真正变化（兼容旧数据格式）
            current = current_user.preferred_css or ''
            if preferred_css_new != current:
                updates['preferred_css'] = preferred_css_new

            # ==================== 执行数据库更新 ====================
            if updates:
                with get_db_connection() as conn:
                    set_clause = ', '.join([f"{k} = ?" for k in updates])
                    values = list(updates.values()) + [current_user.id]
                    conn.execute(f"UPDATE user SET {set_clause} WHERE id = ?", values)
                    conn.commit()

                # 更新当前用户对象（确保后续请求使用新值）
                for k, v in updates.items():
                    setattr(current_user, k, v)

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
        available_themes=available_themes  # 确保模板一定能拿到完整列表
    )
