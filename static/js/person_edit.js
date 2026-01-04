// static/js/person_edit.js
// 人员编辑页面专用 JS：所有联动逻辑 + 照片预览（最新版：其他证件类型 + 证件号联动）

document.addEventListener('DOMContentLoaded', function () {
    // 1. 照片预览（最多 3 张，包含已有照片数量限制）
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
                    div.className = 'position-relative me-3 mb-3';
                    const img = document.createElement('img');
                    img.src = ev.target.result;
                    img.className = 'rounded shadow';
                    img.style = 'width:180px;height:180px;object-fit:cover;';
                    div.appendChild(img);
                    const small = document.createElement('small');
                    small.className = 'd-block text-center mt-1 text-muted';
                    small.textContent = file.name;
                    div.appendChild(small);
                    container.appendChild(div);
                };
                reader.readAsDataURL(file);
                added++;
            }
        });
    }

    previewImages('input[name="images"]', '#preview-container', 3);

    // 2. 户籍小区选择联动：选“外地户籍”时显示详细地址
    const householdSelect = document.getElementById('household_building_select');
    const householdAddressGroup = document.getElementById('household_address_group');
    if (householdSelect && householdAddressGroup) {
        householdSelect.addEventListener('change', function() {
            if (this.value === 'external') {
                householdAddressGroup.style.display = 'block';
            } else {
                householdAddressGroup.style.display = 'none';
                householdAddressGroup.querySelector('input[name="household_address"]').value = '';
            }
        });
    }

    // 3. 是否重点人员开关联动
    const keyPersonSwitch = document.getElementById('is_key_person');
    const keyCategoriesGroup = document.getElementById('key_categories_group');
    if (keyPersonSwitch && keyCategoriesGroup) {
        keyPersonSwitch.addEventListener('change', function() {
            keyCategoriesGroup.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                keyCategoriesGroup.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
            }
        });
    }

    // 4. 是否人户分离开关联动
    const separatedSwitch = document.getElementById('is_separated');
    const residenceGroup = document.getElementById('current_residence_group');
    if (separatedSwitch && residenceGroup) {
        separatedSwitch.addEventListener('change', function() {
            residenceGroup.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                residenceGroup.querySelector('input[name="current_residence"]').value = '';
            }
        });
    }

    // 5. 是否已迁出联动
    const migratedSwitch = document.getElementById('is_migrated_out');
    const migrationGroup = document.getElementById('migration_group');
    if (migratedSwitch && migrationGroup) {
        migratedSwitch.addEventListener('change', function() {
            migrationGroup.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                migrationGroup.querySelectorAll('input').forEach(input => input.value = '');
            }
        });
    }

    // 6. 是否已死亡联动
    const deceasedSwitch = document.getElementById('is_deceased');
    const deathGroup = document.getElementById('death_group');
    if (deceasedSwitch && deathGroup) {
        deceasedSwitch.addEventListener('change', function() {
            deathGroup.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                deathGroup.querySelector('input[name="death_date"]').value = '';
            }
        });
    }

    // 7. 是否使用其他证件开关联动（新增）
    const otherIdSwitch = document.getElementById('has_other_id');
    const otherIdGroup = document.getElementById('other_id_group');
    if (otherIdSwitch && otherIdGroup) {
        otherIdSwitch.addEventListener('change', function() {
            otherIdGroup.style.display = this.checked ? 'block' : 'none';
            if (!this.checked) {
                otherIdGroup.querySelector('select[name="other_id_type"]').value = '';
                otherIdGroup.querySelector('input[name="passport"]').value = '';
            }
        });
    }
});
