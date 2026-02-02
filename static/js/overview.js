// static/js/overview.js
// 首页概览仪表盘图表初始化脚本

document.addEventListener('DOMContentLoaded', function () {
    console.log('【overview.js】页面已加载，开始初始化图表');

    // 从全局变量获取后端传入的数据（在模板中注入）
    const chartData = window.chartData || {
        person_type: [],
        building_type: [],
        grid_person: { names: [], counts: [] }
    };

    console.log('【overview.js】后端传入的 chartData：', chartData);

    // 空数据处理函数
    function getSafeData(data) {
        if (!data || data.length === 0) {
            return [{ name: '暂无数据', value: 1, itemStyle: { color: '#ccc' } }];
        }
        return data;
    }

    // 1. 人员类型分布（饼图）
    const personTypeChart = echarts.init(document.getElementById('personTypeChart'), 'macarons');
    personTypeChart.setOption({
        title: { text: '人员类型分布', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', left: 'left', top: 'middle' },
        series: [{
            name: '人员类型',
            type: 'pie',
            radius: '65%',
            center: ['50%', '50%'],
            data: getSafeData(chartData.person_type),
            emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } }
        }]
    });
    console.log('人员类型图表已初始化');

    // 2. 建筑类型分布（环形图）
    const buildingTypeChart = echarts.init(document.getElementById('buildingTypeChart'), 'macarons');
    buildingTypeChart.setOption({
        title: { text: '建筑类型分布', left: 'center' },
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', left: 'left', top: 'middle' },
        series: [{
            name: '建筑类型',
            type: 'pie',
            radius: ['40%', '70%'],
            center: ['50%', '50%'],
            data: getSafeData(chartData.building_type),
            emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } }
        }]
    });
    console.log('建筑类型图表已初始化');

    // 3. 各网格人员数量（柱状图）
    const gridChart = echarts.init(document.getElementById('gridChart'), 'macarons');
    const gridNames = chartData.grid_person.names.length > 0 ? chartData.grid_person.names : ['暂无网格'];
    const gridCounts = chartData.grid_person.counts.length > 0 ? chartData.grid_person.counts : [0];

    gridChart.setOption({
        title: { text: '各网格人员数量', left: 'center' },
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
        xAxis: {
            type: 'category',
            data: gridNames,
            axisTick: { alignWithLabel: true },
            axisLabel: { interval: 0, rotate: 30 }
        },
        yAxis: { type: 'value', name: '人数' },
        series: [{
            name: '人员数量',
            type: 'bar',
            barWidth: '60%',
            data: gridCounts,
            itemStyle: { color: '#5470C6' },
            label: { show: true, position: 'top' }
        }]
    });
    console.log('网格人员柱状图已初始化');

    // 窗口大小变化时重绘图表
    window.addEventListener('resize', function () {
        personTypeChart.resize();
        buildingTypeChart.resize();
        gridChart.resize();
    });
});
