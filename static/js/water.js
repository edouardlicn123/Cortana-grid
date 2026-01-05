// static/js/water.js
// 永久可见、防篡改水印 - 无论是否打开 F12 都始终显示

(function () {
    'use strict';

    let username = window.watermarkUsername || '未知用户';
    const displayName = username.trim();

    // 水印文本（可自定义格式）
    const watermarkText = displayName;

    // 配置：调整密度、颜色、大小
    const config = {
        tileWidth: 180,    // 横向间距（越小越密）
        tileHeight: 80,    // 纵向间距
        fontSize: 14,      // 字体大小
        opacity: 0.18,     // 透明度（0.1~0.3 推荐）
        rotate: -25,       // 倾斜角度
        color: '#888888'   // 灰色，低调但清晰
    };

    function createWatermarkOverlay() {
        // 如果已存在，先移除旧的（防止重复）
        const existing = document.getElementById('permanent-watermark-overlay');
        if (existing) existing.remove();

        const overlay = document.createElement('div');
        overlay.id = 'permanent-watermark-overlay';

        // 创建 canvas 生成水印图案
        const canvas = document.createElement('canvas');
        canvas.width = config.tileWidth * 3;
        canvas.height = config.tileHeight * 3;

        const ctx = canvas.getContext('2d');
        ctx.font = `${config.fontSize}px Arial, "Microsoft YaHei", sans-serif`;
        ctx.fillStyle = config.color;
        ctx.globalAlpha = config.opacity;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // 多点绘制，形成密集砖墙效果
        const positions = [
            [config.tileWidth, config.tileHeight],
            [config.tileWidth * 2, config.tileHeight * 2],
            [config.tileWidth, config.tileHeight * 2],
            [config.tileWidth * 2, config.tileHeight],
            [config.tileWidth * 1.5, config.tileHeight * 1.5]
        ];

        positions.forEach(([x, y]) => {
            ctx.save();
            ctx.translate(x, y);
            ctx.rotate(config.rotate * Math.PI / 180);
            ctx.fillText(watermarkText, 0, 0);
            ctx.restore();
        });

        // 设置样式：最高层、不可交互、固定背景
        overlay.style.cssText = `
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 100vw !important;
            height: 100vh !important;
            pointer-events: none !important;
            z-index: 999999 !important;
            background-image: url(${canvas.toDataURL('image/png')}) !important;
            background-repeat: repeat !important;
            background-size: ${config.tileWidth}px ${config.tileHeight}px !important;
            image-rendering: crisp-edges !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        `;

        // 插入到 body 最顶部（确保在最上层）
        document.body.insertBefore(overlay, document.body.firstChild);

        console.log('%c 水印已启用：' + displayName, 'color: #888; font-size: 12px;');
    }

    // ============ 强制防移除机制 ============

    // 1. 页面加载时立即创建
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWatermarkOverlay);
    } else {
        createWatermarkOverlay();
    }

    // 2. 窗口加载完成后再次确保存在
    window.addEventListener('load', createWatermarkOverlay);

    // 3. 每 2 秒检查一次，如果被移除就恢复
    setInterval(() => {
        if (!document.getElementById('permanent-watermark-overlay')) {
            createWatermarkOverlay();
        }
    }, 2000);

    // 4. 监控 DOM 变化，防止被删除或修改样式
    const observer = new MutationObserver((mutations) => {
        let shouldRestore = false;

        for (const mutation of mutations) {
            if (mutation.type === 'childList') {
                // 检查是否移除了水印层
                if (!document.getElementById('permanent-watermark-overlay')) {
                    shouldRestore = true;
                }
            }

            if (mutation.type === 'attributes' && mutation.target.id === 'permanent-watermark-overlay') {
                const target = mutation.target;
                // 如果被隐藏、透明、去掉背景等
                if (
                    target.style.display === 'none' ||
                    target.style.visibility === 'hidden' ||
                    target.style.opacity === '0' ||
                    target.style.pointerEvents !== 'none' ||
                    !target.style.backgroundImage
                ) {
                    shouldRestore = true;
                }
            }
        }

        if (shouldRestore) {
            createWatermarkOverlay();
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });

    // 5. 防止通过 console.clear() 或其他方式干扰
    const originalLog = console.log;
    console.log = function (...args) {
        if (args[0] && args[0].includes && args[0].includes('水印已启用')) {
            originalLog.apply(console, args);
        } else {
            originalLog.apply(console, args);
        }
    };

})();
