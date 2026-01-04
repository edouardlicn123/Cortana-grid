// static/js/settings.js
// 系统设置页面专用 JS（角色权限管理 Tab 逻辑）

document.addEventListener('DOMContentLoaded', function () {
    const roleSelect = document.getElementById('roleSelect');
    const table = document.getElementById('permissionsTable');
    const roleNameSpan = document.getElementById('currentRoleName');
    const restoreBtn = document.getElementById('restoreDefaultBtn');

    if (!roleSelect || !table || !roleNameSpan || !restoreBtn) {
        return; // 页面没有权限管理 Tab，直接返回
    }

    // 后端传入的角色权限数据（Jinja2 渲染）
    const rolePermissions = window.rolePermissions || {};

    roleSelect.addEventListener('change', function () {
        const roleId = this.value;
        if (!roleId) {
            table.style.display = 'none';
            return;
        }

        table.style.display = 'block';
        const roleName = this.options[this.selectedIndex].text;
        roleNameSpan.textContent = roleName;

        // 清空所有 checkbox
        document.querySelectorAll('#permissionsTable input[type="checkbox"]').forEach(cb => {
            cb.checked = false;
        });

        // 勾选当前角色拥有的权限
        const currentPerms = rolePermissions[roleId] || [];
        currentPerms.forEach(perm => {
            const checkbox = document.querySelector(`input[name="permissions"][value="${perm}"]`);
            if (checkbox) {
                checkbox.checked = true;
            }
        });
    });

    // 恢复默认权限按钮
    restoreBtn.addEventListener('click', function () {
        if (!confirm('确定要将当前选中角色的权限恢复为系统默认值吗？此操作不可撤销。')) {
            return;
        }

        const form = this.closest('form');
        const hidden = document.createElement('input');
        hidden.type = 'hidden';
        hidden.name = 'action';
        hidden.value = 'restore_default';
        form.appendChild(hidden);
        form.submit();
    });
});
