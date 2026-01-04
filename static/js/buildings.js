// static/js/buildings.js
// 小区/建筑管理页面专用 JS：控制“添加”按钮启用状态

document.addEventListener('DOMContentLoaded', () => {
    const nameInput = document.getElementById('buildingName');
    const typeSelect = document.getElementById('buildingType');
    const gridSelect = document.getElementById('gridSelect');
    const submitBtn = document.getElementById('submitBtn');

    if (!nameInput || !typeSelect || !gridSelect || !submitBtn) {
        return; // 页面没有这些元素时直接返回
    }

    const updateButton = () => {
        submitBtn.disabled = !(nameInput.value.trim() && typeSelect.value && gridSelect.value);
    };

    nameInput.addEventListener('input', updateButton);
    typeSelect.addEventListener('change', updateButton);
    gridSelect.addEventListener('change', updateButton);

    // 初始状态
    updateButton();
});
