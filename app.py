# app.py
# 主应用文件 - Cortana Grid v2.0 极简三分层最终版（2026-01-03 更新：导入导出独立目录）

import os
import logging
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from datetime import datetime

# ====================== Flask 应用创建 ======================
app = Flask(__name__)

# 路径设置
APP_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_PATH = os.path.join(APP_DIR, 'instance')
UPLOAD_FOLDER = os.path.join(APP_DIR, 'static', 'uploads')

# 新增：独立的导入导出目录（项目根目录下 downloads）
DOWNLOADS_FOLDER = os.path.join(APP_DIR, 'downloads')
IMPORTS_FOLDER = os.path.join(DOWNLOADS_FOLDER, 'imports')
EXPORTS_FOLDER = os.path.join(DOWNLOADS_FOLDER, 'exports')

app.instance_path = INSTANCE_PATH
os.makedirs(INSTANCE_PATH, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DOWNLOADS_FOLDER, exist_ok=True)
os.makedirs(IMPORTS_FOLDER, exist_ok=True)
os.makedirs(EXPORTS_FOLDER, exist_ok=True)

# 日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('cortana_grid')
logger.info(f"instance_path: {app.instance_path}")
logger.info(f"upload_folder: {UPLOAD_FOLDER}")
logger.info(f"downloads_folder: {DOWNLOADS_FOLDER}")
logger.info(f"imports_folder: {IMPORTS_FOLDER}")
logger.info(f"exports_folder: {EXPORTS_FOLDER}")

# ====================== 配置 ======================
app.config['SECRET_KEY'] = 'your-super-secret-key-change-in-production'
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOADS_FOLDER'] = DOWNLOADS_FOLDER
app.config['IMPORTS_FOLDER'] = IMPORTS_FOLDER
app.config['EXPORTS_FOLDER'] = EXPORTS_FOLDER
app.jinja_env.add_extension('jinja2.ext.do')

# ====================== 数据库初始化（启动时强制执行） ======================
with app.app_context():
    from utils import init_db
    init_db()
    logger.info("数据库初始化完成（启动时强制执行）")

# ====================== Flask-Login ======================
from repositories.user_model import User, AnonymousUser
from repositories.user_repo import get_user_by_id

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'
login_manager.login_message_category = 'warning'

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    user_row = get_user_by_id(int(user_id))
    return User(user_row) if user_row else None

# ====================== 每个请求前加载用户权限 ======================
@app.before_request
def load_user_permissions():
    if current_user.is_authenticated:
        current_user.load_permissions()

# ====================== 数据库关闭 ======================
from repositories.base import close_db

@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)

# ====================== 全局上下文处理器 ======================
@app.context_processor
def inject_global_vars():
    community_name = '阳光社区'
    show_settings = False
    available_themes = ['style.css']

    try:
        from repositories.settings_repo import get_setting
        community_name = get_setting('community_name', '阳光社区')

        if current_user.is_authenticated:
            show_settings = current_user.has_permission('system:view')

        themes_dir = os.path.join(app.static_folder, 'themes')
        if os.path.isdir(themes_dir):
            theme_files = [f for f in os.listdir(themes_dir) if f.lower().endswith('.css')]
            available_themes.extend([f'themes/{f}' for f in sorted(theme_files)])

    except Exception as e:
        logger.warning(f"全局变量注入异常: {e}")

    return dict(
        community_name=community_name,
        show_settings=show_settings,
        current_user=current_user,
        current_year=datetime.now().year,
        available_themes=available_themes
    )

# ====================== 蓝图注册 ======================
from routes.auth import auth_bp
from routes.main import main_bp
from routes.person import person_bp
from routes.building import building_bp
from routes.grid import grid_bp
from routes.import_export import import_export_bp
from routes.settings import settings_bp
from routes.system_settings import system_settings_bp



app.register_blueprint(auth_bp)
app.register_blueprint(main_bp)
app.register_blueprint(person_bp)
app.register_blueprint(building_bp)
app.register_blueprint(grid_bp)
app.register_blueprint(import_export_bp)
app.register_blueprint(settings_bp)
app.register_blueprint(system_settings_bp)


# ====================== 导入导出初始化 ======================
try:
    from routes.import_export import init_import_export_handlers
    init_import_export_handlers(app)
except Exception as e:
    logger.warning(f'导入导出初始化失败: {e}')

# ====================== 错误处理 ======================
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    flash('权限不足，无法访问该页面', 'error')
    return redirect(url_for('main.overview'))

@app.errorhandler(500)
def internal_error(e):
    logger.error(f'服务器内部错误: {e}')
    return render_template('errors/500.html'), 500

# ====================== 根路由 ======================
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.overview'))
    return redirect(url_for('auth.login'))

# ====================== 启动 ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=True)
