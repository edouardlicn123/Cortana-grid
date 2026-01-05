// static/js/water.js - 优化版：稀疏、轻量、防移除、无卡顿（2026-01-05）
(function () {
    'use strict';

    const username = (window.watermarkUsername || '未知用户').trim() || '未知用户';
    const watermarkText = username;

    const config = {
        tileWidth: 100,    // 横向距离
        tileHeight: 80,   // 纵向距离
        fontSize: 20,     // 字体大小
        opacity: 0.2,     // 透明度
        rotate: -22,      //旋转
        color: '#aaaaaa'   // 颜色
    };

    let overlay = null;

    function createWatermark() {
        // 移除旧的
        if (overlay && overlay.parentNode) {
            overlay.parentNode.removeChild(overlay);
        }

        overlay = document.createElement('div');
        overlay.id = 'permanent-watermark-overlay';

        const canvas = document.createElement('canvas');
        canvas.width = config.tileWidth;
        canvas.height = config.tileHeight;

        const ctx = canvas.getContext('2d');
        ctx.font = `${config.fontSize}px "Microsoft YaHei", Arial, sans-serif`;
        ctx.fillStyle = config.color;
        ctx.globalAlpha = config.opacity;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // 只在中心绘制一个水印文字（不再画5个）
        ctx.save();
        ctx.translate(config.tileWidth / 2, config.tileHeight / 2);
        ctx.rotate(config.rotate * Math.PI / 180);
        ctx.fillText(watermarkText, 0, 0);
        ctx.restore();

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
            image-rendering: pixelated !important;
        `;

        document.body.appendChild(overlay);
    }

    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createWatermark);
    } else {
        createWatermark();
    }
    window.addEventListener('load', createWatermark);

    // 防移除：轻量定时检查（每5秒一次，不卡）
    setInterval(() => {
        if (!document.getElementById('permanent-watermark-overlay')) {
            createWatermark();
        }
    }, 5000);

    // MutationObserver 只监控关键变化
    const observer = new MutationObserver(mutations => {
        for (const mut of mutations) {
            if (mut.type === 'childList' && !document.getElementById('permanent-watermark-overlay')) {
                createWatermark();
                return;
            }
            if (mut.type === 'attributes' && mut.target.id === 'permanent-watermark-overlay') {
                createWatermark();
                return;
            }
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style']
    });

})();
