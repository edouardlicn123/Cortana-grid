# utils.py
# 工具函数模块（完整最终版 - 2026-01-03）
# 新增：init_db 时确保 community_admin 和 grid_user 角色存在

import os
import logging
from werkzeug.security import generate_password_hash

logger = logging.getLogger('cortana_grid')
logger.setLevel(logging.INFO)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def init_db():
    db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance', 'community_system.sqlite')

    from repositories.base import get_db_connection

    with get_db_connection() as conn:
        schema_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        
        conn.commit()

        logger.info("确保默认超级管理员存在...")

        default_password = 'a12345678'
        hashed_password = generate_password_hash(default_password)

        conn.execute('''
            INSERT OR IGNORE INTO user 
            (username, password_hash, full_name, is_active, must_change_password, page_size, preferred_css)
            VALUES (?, ?, ?, 1, 1, 20, '')
        ''', ('admin', hashed_password, '超级管理员'))

        # 确保所有必要角色存在
        conn.execute("INSERT OR IGNORE INTO role (name) VALUES ('super_admin')")
        conn.execute("INSERT OR IGNORE INTO role (name) VALUES ('community_admin')")
        conn.execute("INSERT OR IGNORE INTO role (name) VALUES ('grid_user')")

        # 为 admin 用户分配 super_admin 角色
        conn.execute('''
            INSERT OR IGNORE INTO user_role (user_id, role_id)
            SELECT u.id, r.id FROM user u, role r 
            WHERE u.username = 'admin' AND r.name = 'super_admin'
        ''')

        # 为 super_admin 角色分配全权限兜底（防止权限为空）
        super_admin_row = conn.execute("SELECT id FROM role WHERE name = 'super_admin'").fetchone()
        if super_admin_row:
            conn.execute('''
                INSERT OR IGNORE INTO role_permission (role_id, permission)
                VALUES (?, '*:*')
            ''', (super_admin_row['id'],))

        # 系统设置初始化
        conn.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('community_name', '阳光社区')
        ''')
        conn.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('default_page_size', '20')
        ''')
        conn.execute('''
            INSERT OR IGNORE INTO settings (key, value) 
            VALUES ('show_default_credentials', '0')
        ''')

        conn.commit()
        logger.info("数据库初始化完成：默认管理员、所有角色及系统设置已就绪")
