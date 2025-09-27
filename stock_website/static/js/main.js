// ============================================
// 全局变量
// ============================================
let stocksData = [];
let currentSortColumn = '';
let sortDirection = 'asc';
let currentPage = 1;
let itemsPerPage = 100;  // 每页显示100只股票

// ============================================
// 页面加载完成后执行
// ============================================
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    initializeTheme();
    startTimeDisplay();
    loadStockData();
    setupEventListeners();
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
// 时间显示功能
// ============================================
function startTimeDisplay() {
    updateTime();
    setInterval(updateTime, 1000);
}

function updateTime() {
    const now = new Date();
    const timeString = now.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });

    document.getElementById('current-time').textContent = timeString;
}

// ============================================
// 股票数据加载
// ============================================
async function loadStockData() {
    const loadingElement = document.getElementById('loading');
    const tableContainer = document.getElementById('table-container');
    const errorMessage = document.getElementById('error-message');

    try {
        loadingElement.style.display = 'flex';
        tableContainer.style.display = 'none';
        errorMessage.style.display = 'none';

        const response = await fetch('/api/stocks');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        stocksData = data;
        displayStockData(stocksData);

        loadingElement.style.display = 'none';
        tableContainer.style.display = 'block';

    } catch (error) {
        console.error('Error loading stock data:', error);
        showError('加载股票数据失败: ' + error.message);
        loadingElement.style.display = 'none';
    }
}

function displayStockData(data) {
    const tbody = document.getElementById('stock-tbody');
    tbody.innerHTML = '';

    // 计算分页
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const pageData = data.slice(startIndex, endIndex);

    pageData.forEach(stock => {
        const row = createStockRow(stock);
        tbody.appendChild(row);
    });

    // 更新分页信息
    updatePaginationInfo(data.length);
}

function createStockRow(stock) {
    const row = document.createElement('tr');
    row.className = 'fade-in';

    // 判断涨跌样式
    let changeClass = 'price-neutral';
    let changePrefix = '';

    if (stock.change_pct > 0) {
        changeClass = 'price-up';
        changePrefix = '+';
    } else if (stock.change_pct < 0) {
        changeClass = 'price-down';
    }

    row.innerHTML = `
        <td class="number">${stock.id}</td>
        <td class="number en-font">${stock.stock_code}</td>
        <td>
            <a href="/stock_detail/${stock.ts_code}" class="stock-name-link">
                ${stock.stock_name}
            </a>
        </td>
        <td class="number en-font ${changeClass}">
            ${changePrefix}${stock.change_pct.toFixed(2)}%
        </td>
        <td class="number en-font ${changeClass}">
            ¥${stock.current_price.toFixed(2)}
        </td>
        <td class="number en-font">
            ${stock.volume_ratio.toFixed(2)}
        </td>
        <td class="number en-font">
            ${formatMarketValue(stock.market_value)}
        </td>
        <td class="number en-font">
            ${stock.ttm > 0 ? stock.ttm.toFixed(2) : '-'}
        </td>
    `;

    return row;
}

function updatePaginationInfo(totalItems) {
    const totalPages = Math.ceil(totalItems / itemsPerPage);
    const pageInfo = document.getElementById('page-info');
    const pageControls = document.getElementById('page-controls');

    if (pageInfo) {
        pageInfo.textContent = `第 ${currentPage} 页，共 ${totalPages} 页 (总计 ${totalItems} 只股票)`;
    }

    if (pageControls) {
        const prevBtn = document.getElementById('prev-page');
        const nextBtn = document.getElementById('next-page');

        if (prevBtn) prevBtn.disabled = currentPage <= 1;
        if (nextBtn) nextBtn.disabled = currentPage >= totalPages;
    }
}

function goToPage(page) {
    const totalPages = Math.ceil(stocksData.length / itemsPerPage);
    if (page < 1 || page > totalPages) return;

    currentPage = page;
    displayStockData(stocksData);
}

function formatMarketValue(value) {
    if (value === 0 || !value) return '-';

    // value的单位是万元，转换为亿元显示
    const valueInYi = value / 10000;

    if (valueInYi >= 1000) {
        return (valueInYi / 1000).toFixed(2) + '万亿';
    } else if (valueInYi >= 1) {
        return valueInYi.toFixed(2) + '亿';
    } else {
        return value.toFixed(2) + '万';
    }
}

// ============================================
// 表格排序功能
// ============================================
function setupTableSorting() {
    const headers = document.querySelectorAll('th[data-sort]');

    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort');
            sortTable(column);
        });
    });
}

function sortTable(column) {
    if (currentSortColumn === column) {
        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
    } else {
        currentSortColumn = column;
        sortDirection = 'asc';
    }

    // 更新排序图标
    updateSortIcons(column, sortDirection);

    // 排序数据
    stocksData.sort((a, b) => {
        let valueA = a[column];
        let valueB = b[column];

        // 处理数字类型
        if (typeof valueA === 'number' && typeof valueB === 'number') {
            return sortDirection === 'asc' ? valueA - valueB : valueB - valueA;
        }

        // 处理字符串类型
        valueA = String(valueA).toLowerCase();
        valueB = String(valueB).toLowerCase();

        if (sortDirection === 'asc') {
            return valueA.localeCompare(valueB);
        } else {
            return valueB.localeCompare(valueA);
        }
    });

    // 重新显示当前页数据
    displayStockData(stocksData);
}

function updateSortIcons(activeColumn, direction) {
    // 重置所有图标
    document.querySelectorAll('th[data-sort] i').forEach(icon => {
        icon.className = 'fas fa-sort';
    });

    // 设置当前列的图标
    const activeHeader = document.querySelector(`th[data-sort="${activeColumn}"] i`);
    if (activeHeader) {
        activeHeader.className = direction === 'asc' ? 'fas fa-sort-up' : 'fas fa-sort-down';
    }
}

// ============================================
// 搜索功能
// ============================================
async function searchStock(keyword) {
    if (!keyword.trim()) {
        hideSearchResults();
        return;
    }

    try {
        const response = await fetch(`/api/search_stock/${encodeURIComponent(keyword)}`);

        if (response.status === 404) {
            showSearchResults([]);
            return;
        }

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        showStockModal(data);

    } catch (error) {
        console.error('Error searching stock:', error);
        showError('搜索失败: ' + error.message);
    }
}

function showStockModal(stockData) {
    const modal = document.getElementById('search-modal');
    const stockInfo = document.getElementById('stock-info');

    // 判断涨跌样式
    let changeClass = 'price-neutral';
    let changePrefix = '';

    if (stockData.change_pct > 0) {
        changeClass = 'price-up';
        changePrefix = '+';
    } else if (stockData.change_pct < 0) {
        changeClass = 'price-down';
    }

    stockInfo.innerHTML = `
        <div class="stock-info-grid">
            <div class="stock-info-item">
                <strong>股票代码:</strong>
                <span class="number en-font">${stockData.stock_code}</span>
            </div>
            <div class="stock-info-item">
                <strong>股票名称:</strong>
                <span>${stockData.stock_name}</span>
            </div>
            <div class="stock-info-item">
                <strong>当前价格:</strong>
                <span class="number en-font ${changeClass}">¥${stockData.current_price.toFixed(2)}</span>
            </div>
            <div class="stock-info-item">
                <strong>涨跌幅:</strong>
                <span class="number en-font ${changeClass}">${changePrefix}${stockData.change_pct.toFixed(2)}%</span>
            </div>
            <div class="stock-info-item">
                <strong>行业:</strong>
                <span>${stockData.industry || '-'}</span>
            </div>
            <div class="stock-info-item">
                <strong>地区:</strong>
                <span>${stockData.area || '-'}</span>
            </div>
            <div class="stock-info-item">
                <strong>市值:</strong>
                <span class="number en-font">${formatMarketValue(stockData.market_value)}</span>
            </div>
            <div class="stock-info-item">
                <strong>市盈率TTM:</strong>
                <span class="number en-font">${stockData.ttm > 0 ? stockData.ttm.toFixed(2) : '-'}</span>
            </div>
            <div class="stock-actions">
                <a href="/stock_detail/${stockData.ts_code}" class="btn-detail">查看详情</a>
            </div>
        </div>
    `;

    modal.style.display = 'block';
}

function showSearchResults(results) {
    const searchResults = document.getElementById('search-results');

    if (results.length === 0) {
        searchResults.innerHTML = '<div class="no-results">未找到相关股票</div>';
        searchResults.style.display = 'block';
        return;
    }

    // 这里可以实现下拉搜索建议功能
    searchResults.style.display = 'none';
}

function hideSearchResults() {
    document.getElementById('search-results').style.display = 'none';
}

// ============================================
// 事件监听器设置
// ============================================
function setupEventListeners() {
    // 主题切换
    document.getElementById('theme-toggle-btn').addEventListener('click', toggleTheme);

    // 搜索功能
    const searchInput = document.getElementById('search-input');
    const searchBtn = document.getElementById('search-btn');

    searchBtn.addEventListener('click', () => {
        const keyword = searchInput.value.trim();
        if (keyword) {
            searchStock(keyword);
        }
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const keyword = searchInput.value.trim();
            if (keyword) {
                searchStock(keyword);
            }
        }
    });

    // 模态框关闭
    const modal = document.getElementById('search-modal');
    const closeBtn = document.getElementById('close-modal');

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // 表格排序
    setupTableSorting();

    // 点击其他地方隐藏搜索结果
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-container')) {
            hideSearchResults();
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

    // 5秒后自动隐藏错误信息
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

// ============================================
// 添加CSS样式到页面
// ============================================
function addCustomStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .stock-info-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }

        .stock-info-item {
            padding: 10px;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 6px;
        }

        .stock-actions {
            grid-column: 1 / -1;
            text-align: center;
            margin-top: 20px;
        }

        .btn-detail {
            display: inline-block;
            padding: 12px 24px;
            background-color: var(--primary-color);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background-color 0.3s ease;
        }

        .btn-detail:hover {
            background-color: var(--hover-color);
        }

        .no-results {
            padding: 15px;
            text-align: center;
            color: var(--text-secondary);
        }

        @media (max-width: 768px) {
            .stock-info-grid {
                grid-template-columns: 1fr;
            }
        }
    `;
    document.head.appendChild(style);
}

// 页面加载时添加自定义样式
document.addEventListener('DOMContentLoaded', addCustomStyles);