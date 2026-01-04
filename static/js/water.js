(function () {
    let username = window.watermarkUsername || '未知用户';  // 这里实际注入的是 real_name

    function createWatermark() {
        // 组合显示：用户名(作为备用) + 真实姓名
        // 如果 real_name 为空，则只显示 username
        const displayName = username.trim();
        const text = displayName;  // 可以根据需要改成 `${current_user.username} ${displayName}`

        // 砖块叠加极密设置
        const tileWidth = 120;   // 越小越密，可继续调小到 110 或 100
        const tileHeight = 50;

        const canvas = document.createElement('canvas');
        canvas.width = tileWidth * 2;   // 双倍用于错位叠加
        canvas.height = tileHeight * 2;

        const ctx = canvas.getContext('2d');

        // 多层错位绘制同一姓名，实现砖墙式密集叠加
        const positions = [
            {x: tileWidth / 2, y: tileHeight / 2},                   // 主位置
            {x: tileWidth / 2 + tileWidth, y: tileHeight / 2},       // 右偏移
            {x: tileWidth / 2, y: tileHeight / 2 + tileHeight},     // 下偏移
            {x: tileWidth / 2 + tileWidth, y: tileHeight / 2 + tileHeight}, // 对角
            {x: tileWidth, y: tileHeight},                         // 额外叠加增强密度
        ];

        positions.forEach(pos => {
            ctx.save();
            ctx.translate(pos.x, pos.y);
            ctx.rotate(-30 * Math.PI / 180);  // 倾斜角度
            ctx.font = '11px Arial, sans-serif';  // 视觉约 10px，小巧清晰
            ctx.fillStyle = 'rgba(145, 145, 145, 0.21)';  // 淡灰，低调专业
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(text, 0, 0);
            ctx.restore();
        });

        const overlay = document.getElementById('watermark-overlay');
        if (overlay) {
            overlay.style.backgroundImage = `url(${canvas.toDataURL('image/png')})`;
        }
    }

    function initWatermark() {
        if (document.getElementById('watermark-overlay')) return;

        const overlay = document.createElement('div');
        overlay.id = 'watermark-overlay';
        overlay.style.cssText = `
            position: fixed !important;
            top: 0 !important; left: 0 !important;
            width: 100vw !important; height: 100vh !important;
            pointer-events: none !important;
            z-index: 9999 !important;
            background-repeat: repeat !important;
            background-size: ${tileWidth}px ${tileHeight}px !important;
            image-rendering: crisp-edges !important;
            image-rendering: pixelated !important;
        `;
        document.body.appendChild(overlay);
        createWatermark();
    }

    // 防篡改观察器（被删除或隐藏立即恢复）
    const observer = new MutationObserver((mutations) => {
        let needRestore = false;
        mutations.forEach((mutation) => {
            if (mutation.type === 'childList' && !document.getElementById('watermark-overlay')) {
                needRestore = true;
            }
            if (mutation.type === 'attributes' && mutation.target.id === 'watermark-overlay') {
                const target = mutation.target;
                if (target.style.display === 'none' || target.style.opacity === '0' ||
                    target.style.visibility === 'hidden' || !target.style.backgroundImage) {
                    needRestore = true;
                }
            }
        });
        if (needRestore) {
            const existing = document.getElementById('watermark-overlay');
            if (existing) existing.parentNode.removeChild(existing);
            initWatermark();
        }
    });

    observer.observe(document.body, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });

    window.addEventListener('load', initWatermark);
    window.addEventListener('resize', createWatermark);

    // 检测姓名变化（切换用户时刷新）
    setInterval(() => {
        if (window.watermarkUsername !== username) {
            username = window.watermarkUsername || '未知用户';
            createWatermark();
        }
    }, 1000);
})();
