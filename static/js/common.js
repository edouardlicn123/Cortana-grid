// static/js/common.js
// 全局公共 JS 函数库（所有页面加载）

// 1. 动态显示/隐藏字段（通用）
function toggleField(checkboxId, targetIds, clear = true) {
    const checkbox = document.getElementById(checkboxId);
    if (!checkbox) return;

    const targets = targetIds.map(id => document.getElementById(id)).filter(el => el);

    function update() {
        const show = checkbox.checked;
        targets.forEach(el => {
            el.style.display = show ? 'block' : 'none';
            if (clear && !show) {
                el.querySelectorAll('input, textarea, select').forEach(input => {
                    if (input.type === 'checkbox' || input.type === 'radio') {
                        input.checked = false;
                    } else {
                        input.value = '';
                    }
                });
            }
        });
    }

    update();
    checkbox.addEventListener('change', update);
}

// 2. 一键复制表格到剪贴板
function copyTableToClipboard(tableId, button) {
    const table = document.getElementById(tableId);
    if (!table) return;

    let text = '';
    table.querySelectorAll('tr').forEach(row => {
        const cells = Array.from(row.cells).map(cell => cell.textContent.trim());
        text += cells.join('\t') + '\n';
    });

    navigator.clipboard.writeText(text).then(() => {
        showCopyFeedback(button, button.innerHTML);
    }).catch(() => {
        alert('复制失败，请手动选择表格内容复制');
    });
}

// 3. 复制成功反馈（按钮变化 2 秒）
function showCopyFeedback(button, originalHTML) {
    if (!button) return;
    const origHTML = originalHTML || button.innerHTML;
    button.innerHTML = '<i class="bi bi-check-circle me-2"></i>已复制！';
    button.classList.replace('btn-outline-secondary', 'btn-success');
    setTimeout(() => {
        button.innerHTML = origHTML;
        button.classList.replace('btn-success', 'btn-outline-secondary');
    }, 2000);
}

// 4. 多张照片上传预览（限制总数）
function previewImages(inputSelector, containerSelector, maxImages = 3) {
    const input = document.querySelector(inputSelector);
    const container = document.querySelector(containerSelector);
    if (!input || !container) return;

    const existingCount = container.querySelectorAll('img').length;

    input.addEventListener('change', function(e) {
        const files = e.target.files;
        let added = 0;

        for (let file of files) {
            if (!file.type.startsWith('image/')) continue;
            if (existingCount + added >= maxImages) {
                alert(`照片最多 ${maxImages} 张`);
                break;
            }

            const reader = new FileReader();
            reader.onload = ev => {
                const div = document.createElement('div');
                div.className = 'text-center';
                const img = document.createElement('img');
                img.src = ev.target.result;
                img.className = 'rounded shadow-sm';
                img.style = 'width:150px;height:150px;object-fit:cover;';
                div.appendChild(img);
                div.appendChild(document.createTextNode(file.name));
                container.appendChild(div);
            };
            reader.readAsDataURL(file);
            added++;
        }
    });
}

// 页面加载完成后可自动初始化（可选扩展）
document.addEventListener('DOMContentLoaded', function() {
    // 可在此处添加自动绑定逻辑，例如 data 属性
});
