// static/js/import_export.js
// 导入导出页面专用 JS

document.addEventListener('DOMContentLoaded', function () {
    const select = document.getElementById('dataTypeSelect');
    const container = document.getElementById('template-container');
    const exportBtn = document.getElementById('exportBtn');
    const importTypeSlug = document.getElementById('importTypeSlug');

    if (!select || !container || !exportBtn || !importTypeSlug) return;

    // 模板路径（由后端渲染）
    const templatePaths = window.templatePaths || {};

    function loadTemplate(type) {
        container.innerHTML = `
            <div class="text-center py-5 text-muted">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">加载中...</span>
                </div>
                <p class="mt-3">加载范例中...</p>
            </div>`;

        fetch(templatePaths[type])
            .then(response => {
                if (!response.ok) throw new Error('网络错误');
                return response.text();
            })
            .then(html => {
                container.innerHTML = html;
                bindCopyButtons();
            })
            .catch(err => {
                container.innerHTML = `<div class="alert alert-danger mt-4">加载范例失败：${err.message}</div>`;
            });
    }

    function bindCopyButtons() {
        document.querySelectorAll('.copy-btn').forEach(btn => {
            btn.onclick = function () {
                const tableId = this.dataset.target;
                copyTableToClipboard(tableId, this);
            };
        });
    }

    function updateAll() {
        const type = select.value;
        loadTemplate(type);
        exportBtn.onclick = () => location.href = `/import_export/export/${type}`;
        importTypeSlug.value = type;
    }

    // 初始化
    updateAll();
    select.addEventListener('change', updateAll);
});
