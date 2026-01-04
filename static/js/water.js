
// 全屏用户名水印（砖墙交错版 - background-repeat 可靠实现，2026-01-04）
(function() {
    let username = (window.current_username || '未知用户').trim();
    if (!username) username = 'CortanaGrid';

    // 参数（三倍密度、砖墙交错、固定透明度）
    const fontSize = 22;
    const color = 'rgba(0, 0, 0, 0.03)';
    const angle = -25;
    const density = 120;  // 横向间距
    const rowHeight = 85; // 纵向间距
    const stagger = density / 2; // 交错偏移

    // 生成单层图案（一行多个用户名）
    function createPattern(offset = 0) {
        const canvas = document.createElement('canvas');
        canvas.width = density * 6;  // 足够宽确保无缝
        canvas.height = rowHeight;

        const ctx = canvas.getContext('2d');
        ctx.font = `bold ${fontSize}px Arial`;
        ctx.fillStyle = color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        for (let x = density / 2 + offset; x < canvas.width; x += density) {
            ctx.fillText(username, x, rowHeight / 2);
        }

        return canvas.toDataURL('image/png');
    }

    // 创建全屏层
    function createLayer(offset = 0, z = 9999) {
        const layer = document.createElement('div');
        layer.style.position = 'fixed';
        layer.style.top = '0';
        layer.style.left = '0';
        layer.style.width = '100vw';
        layer.style.height = '100vh';
        layer.style.pointerEvents = 'none';
        layer.style.zIndex = z;
        layer.style.backgroundImage = `url(${createPattern(offset)})`;
        layer.style.backgroundRepeat = 'repeat';
        layer.style.backgroundPosition = '0 0';
        layer.style.transform = `rotate(${angle}deg)`;
        layer.style.transformOrigin = 'center';
        layer.style.opacity = '0.03';
        layer.style.userSelect = 'none';

        document.body.appendChild(layer);
        return layer;
    }

    // 两层实现砖墙交错
    createLayer(0, 9999);     // 正常层
    createLayer(stagger, 9998); // 交错层

    // 定时补层防移除
    setInterval(() => {
        if (document.querySelectorAll('div[style*="z-index: 9999"]').length < 2) {
            createLayer(0, 9999);
            createLayer(stagger, 9998);
        }
    }, 8000);

    // DOM 监控补层
    const observer = new MutationObserver(() => {
        if (document.querySelectorAll('div[style*="z-index: 9999"]').length < 2) {
            createLayer(0, 9999);
            createLayer(stagger, 9998);
        }
    });
    observer.observe(document.body, { childList: true, subtree: true });

})();

