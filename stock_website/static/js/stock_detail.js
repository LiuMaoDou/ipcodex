// ============================================
// 全局变量
// ============================================
let priceChart = null;
let stockData = null;

// ============================================
// 页面加载完成后执行
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    initializeDetailPage();
});

function initializeDetailPage() {
    initializeTheme();
    loadStockDetail();
    setupEventListeners();
}

// ============================================
// 股票详情数据加载
// ============================================
async function loadStockDetail() {
    const loadingElement = document.getElementById('loading');
    const stockInfoCard = document.getElementById('stock-info-card');
    const chartContainer = document.getElementById('chart-container');
    const errorMessage = document.getElementById('error-message');

    try {
        loadingElement.style.display = 'flex';
        stockInfoCard.style.display = 'none';
        chartContainer.style.display = 'none';
        errorMessage.style.display = 'none';

        // 获取股票历史数据
        const response = await fetch(`/api/stock_history/${stockCode}`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const historyData = await response.json();

        if (historyData.error) {
            throw new Error(historyData.error);
        }

        if (!historyData || historyData.length === 0) {
            throw new Error('没有找到股票历史数据');
        }

        // 获取最新的股票基本信息
        await loadStockBasicInfo();

        // 显示图表
        displayPriceChart(historyData);

        loadingElement.style.display = 'none';
        stockInfoCard.style.display = 'block';
        chartContainer.style.display = 'block';

    } catch (error) {
        console.error('Error loading stock detail:', error);
        showError('加载股票详情失败: ' + error.message);
        loadingElement.style.display = 'none';
    }
}

async function loadStockBasicInfo() {
    try {
        // 从股票代码中提取股票名称进行搜索
        const stockNumber = stockCode.substring(0, 6);
        const response = await fetch(`/api/search_stock/${stockNumber}`);

        if (response.ok) {
            stockData = await response.json();
            displayStockInfo(stockData);
        } else {
            // 如果搜索失败，显示基本信息
            displayBasicInfo();
        }
    } catch (error) {
        console.error('Error loading basic info:', error);
        displayBasicInfo();
    }
}

function displayStockInfo(data) {
    // 更新页面标题
    document.title = `股票详情 - ${data.stock_name} (${data.stock_code})`;
    document.getElementById('stock-title').textContent = `${data.stock_name} (${data.stock_code})`;

    // 更新股票信息卡片
    document.getElementById('stock-name').textContent = data.stock_name;
    document.getElementById('stock-code-display').textContent = data.stock_code;

    // 判断涨跌样式
    let changeClass = 'price-neutral';
    let changePrefix = '';

    if (data.change_pct > 0) {
        changeClass = 'price-up';
        changePrefix = '+';
    } else if (data.change_pct < 0) {
        changeClass = 'price-down';
    }

    const priceElement = document.getElementById('current-price');
    const changeElement = document.getElementById('price-change');

    priceElement.textContent = `¥${data.current_price.toFixed(2)}`;
    priceElement.className = `price ${changeClass}`;

    changeElement.textContent = `${changePrefix}${data.change_pct.toFixed(2)}%`;
    changeElement.className = `change ${changeClass}`;
}

function displayBasicInfo() {
    // 显示基本信息
    const stockNumber = stockCode.substring(0, 6);
    document.getElementById('stock-title').textContent = `股票详情 - ${stockNumber}`;
    document.getElementById('stock-name').textContent = '股票信息';
    document.getElementById('stock-code-display').textContent = stockNumber;
    document.getElementById('current-price').textContent = '价格信息加载中...';
    document.getElementById('price-change').textContent = '';
}

// ============================================
// 价格图表显示
// ============================================
function displayPriceChart(historyData) {
    const ctx = document.getElementById('price-chart').getContext('2d');

    // 准备图表数据
    const labels = historyData.map(item => {
        const date = item.date;
        return `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;
    });

    const prices = historyData.map(item => item.close);
    const changePcts = historyData.map(item => item.pct_chg || 0);

    // 获取当前主题
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const isDark = currentTheme === 'dark';

    // 主题相关的颜色
    const colors = {
        text: isDark ? '#ffffff' : '#212529',
        grid: isDark ? '#333333' : '#e9ecef',
        line: '#007bff',
        fill: isDark ? 'rgba(13, 110, 253, 0.1)' : 'rgba(0, 123, 255, 0.1)'
    };

    // 销毁现有图表
    if (priceChart) {
        priceChart.destroy();
    }

    // 创建新图表
    priceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: '收盘价',
                data: prices,
                borderColor: colors.line,
                backgroundColor: colors.fill,
                borderWidth: 2,
                fill: true,
                tension: 0.1,
                pointBackgroundColor: colors.line,
                pointBorderColor: colors.line,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                intersect: false,
                mode: 'index'
            },
            plugins: {
                legend: {
                    display: true,
                    labels: {
                        color: colors.text,
                        font: {
                            family: '"微软雅黑", "Microsoft YaHei", sans-serif',
                            weight: 'bold'
                        }
                    }
                },
                tooltip: {
                    backgroundColor: isDark ? '#1e1e1e' : '#ffffff',
                    titleColor: colors.text,
                    bodyColor: colors.text,
                    borderColor: colors.grid,
                    borderWidth: 1,
                    callbacks: {
                        label: function(context) {
                            const price = context.parsed.y;
                            const changePct = changePcts[context.dataIndex];
                            const changePrefix = changePct > 0 ? '+' : '';
                            return [
                                `收盘价: ¥${price.toFixed(2)}`,
                                `涨跌幅: ${changePrefix}${changePct.toFixed(2)}%`
                            ];
                        }
                    }
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: '交易日期',
                        color: colors.text,
                        font: {
                            family: '"微软雅黑", "Microsoft YaHei", sans-serif',
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        color: colors.text,
                        maxTicksLimit: 10,
                        font: {
                            family: '"Cascadia Code", "Consolas", monospace',
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: colors.grid
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: '价格 (¥)',
                        color: colors.text,
                        font: {
                            family: '"微软雅黑", "Microsoft YaHei", sans-serif',
                            weight: 'bold'
                        }
                    },
                    ticks: {
                        color: colors.text,
                        callback: function(value) {
                            return '¥' + value.toFixed(2);
                        },
                        font: {
                            family: '"Cascadia Code", "Consolas", monospace',
                            weight: 'bold'
                        }
                    },
                    grid: {
                        color: colors.grid
                    }
                }
            }
        }
    });
}

function formatVolume(volume) {
    if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿手';
    } else if (volume >= 10000) {
        return (volume / 10000).toFixed(2) + '万手';
    } else {
        return volume.toLocaleString() + '手';
    }
}

// ============================================
// 主题功能
// ============================================
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeButton(newTheme);

    // 重新绘制图表以应用新主题
    if (priceChart && stockData) {
        setTimeout(() => {
            loadStockDetail();
        }, 100);
    }
}

function updateThemeButton(theme) {
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');

    if (theme === 'dark') {
        themeIcon.className = 'fas fa-sun';
        themeText.textContent = 'Light';
    } else {
        themeIcon.className = 'fas fa-moon';
        themeText.textContent = 'Dark';
    }
}

// ============================================
// 事件监听器设置
// ============================================
function setupEventListeners() {
    // 主题切换
    document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);

    // 窗口大小改变时重新调整图表
    window.addEventListener('resize', () => {
        if (priceChart) {
            priceChart.resize();
        }
    });
}

// ============================================
// 错误处理
// ============================================
function showError(message) {
    const errorMessage = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');

    errorText.textContent = message;
    errorMessage.style.display = 'flex';

    // 10秒后自动隐藏错误信息
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 10000);
}