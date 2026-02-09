// static/js/person_edit.js
// 人员编辑页面专用 JS：所有联动逻辑 + 照片预览（最新版：支持所有新字段的开关联动）

document.addEventListener('DOMContentLoaded', function () {
    // ==================== 1. 照片预览（最多 3 张，包含已有照片数量限制） ====================
    function previewImages(inputSelector, containerSelector, maxImages = 3) {
        const input = document.querySelector(inputSelector);
        const container = document.querySelector(containerSelector);
        if (!input || !container) return;

        // 计算当前已有照片数量（编辑时已有上传的照片）
        const existingCount = container.querySelectorAll('img').length;

        input.addEventListener('change', function(e) {
            const files = e.target.files;
            let added = 0;

            for (let file of files) {
                if (!file.type.startsWith('image/')) continue;
                if (existingCount + added >= maxImages) {
                    alert(`照片最多允许上传 ${maxImages} 张（含已有照片）`);
                    break;
                }

                const reader = new FileReader();
                reader.onload = function(ev) {
                    const div = document.createElement('div');
                    div.className = 'position-relative text-center me-3 mb-3';
                    
                    const img = document.createElement('img');
                    img.src = ev.target.result;
                    img.className = 'rounded shadow';
                    img.style.width = '180px';
                    img.style.height = '180px';
                    img.style.objectFit = 'cover';
                    
                    const small = document.createElement('small');
                    small.className = 'd-block mt-1 text-muted';
                    small.textContent = file.name;
                    
                    div.appendChild(img);
                    div.appendChild(small);
                    container.appendChild(div);
                };
                reader.readAsDataURL(file);
                added++;
            }

            // 清空 input 值，防止重复选择同一文件不触发 change
            input.value = '';
        });
    }

    previewImages('input[name="images"]', '#preview-container', 3);

    // ==================== 2. 开关联动通用函数（可复用） ====================
    function toggleGroup(switchId, groupId, clearOnHide = true) {
        const switchEl = document.getElementById(switchId);
        const groupEl = document.getElementById(groupId);
        if (!switchEl || !groupEl) return;

        const update = () => {
            const isChecked = switchEl.checked;
            groupEl.style.display = isChecked ? 'block' : 'none';
            
            if (!isChecked && clearOnHide) {
                // 清空该组内所有输入框和选择框
                groupEl.querySelectorAll('input[type="text"], input[type="date"], textarea, select').forEach(el => {
                    el.value = '';
                });
                // 清空 checkbox（如果有）
                groupEl.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.checked = false;
                });
            }
        };

        switchEl.addEventListener('change', update);
        // 初始化状态
        update();
    }

    // ==================== 3. 所有开关联动 ====================

    // 是否使用其他证件
    toggleGroup('has_other_id', 'other_id_group');

    // 是否重点人员
    toggleGroup('is_key_person', 'key_categories_group');

    // 人户分离
    toggleGroup('is_separated', 'current_residence_group');

    // 是否已迁出本社区
    toggleGroup('is_migrated_out', 'migration_group');

    // 是否已死亡
    toggleGroup('is_deceased', 'death_group');

    // ==================== 4. 户籍小区选择联动（如果有“外地户籍”选项） ====================
    // 注意：当前 edit_person.html 中户籍建筑是普通 select，没有 external 选项
    // 如果未来添加“外地户籍”特殊值，可启用以下代码
    /*
    const householdSelect = document.querySelector('select[name="household_building_id"]');
    const householdAddressGroup = document.getElementById('household_address_group');
    if (householdSelect && householdAddressGroup) {
        householdSelect.addEventListener('change', function() {
            // 假设添加了 value="external" 的选项
            if (this.value === 'external' || !this.value) {
                householdAddressGroup.style.display = 'block';
            } else {
                householdAddressGroup.style.display = 'none';
                householdAddressGroup.querySelector('input[name="household_address"]').value = '';
            }
        });
    }
    */

    // ==================== 5. 其他增强（可选） ====================
    // 身份证输入时自动提示（如果需要）
    const idCardInput = document.getElementById('id_card');
    if (idCardInput) {
        idCardInput.addEventListener('input', function() {
            this.value = this.value.replace(/\s/g, '').toUpperCase();
        });
    }

    // 出生日期输入格式化提示（可选）
    const birthInput = document.getElementById('birth_date');
    if (birthInput) {
        birthInput.addEventListener('input', function(e) {
            let val = e.target.value.replace(/\D/g, '');
            if (val.length > 8) val = val.slice(0, 8);
            e.target.value = val;
        });
    }

    console.log('人员编辑页面 JS 初始化完成');
});
