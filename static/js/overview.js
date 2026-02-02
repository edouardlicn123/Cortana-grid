// static/js/overview.js
document.addEventListener('DOMContentLoaded', function () {
    // 1. 总人数与类型分布（饼图）
    const personTypeChart = echarts.init(document.getElementById('personTypeChart'));
    personTypeChart.setOption({
        title: { text: '人员类型分布', left: 'center' },
        tooltip: { trigger: 'item' },
        series: [{
            type: 'pie',
            radius: '60%',
            data: window.personStats.types,
            emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } }
        }]
    });

    // 2. 各网格人员数量（柱状图）
    const gridChart = echarts.init(document.getElementById('gridChart'));
    gridChart.setOption({
        title: { text: '各网格人员数量', left: 'center' },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: window.personStats.grid_names },
        yAxis: { type: 'value' },
        series: [{ type: 'bar', data: window.personStats.grid_counts, itemStyle: { color: '#0d6efd' } }]
    });

    // 3. 建筑类型分布（环形图）
    const buildingTypeChart = echarts.init(document.getElementById('buildingTypeChart'));
    buildingTypeChart.setOption({
        title: { text: '建筑类型分布', left: 'center' },
        tooltip: { trigger: 'item' },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            data: window.buildingStats.types
        }]
    });

    // 4. 总体统计卡片已由后端渲染，这里只负责图表
    // 响应式：窗口变化时重绘
    window.addEventListener('resize', () => {
        personTypeChart.resize();
        gridChart.resize();
        buildingTypeChart.resize();
    });
});
