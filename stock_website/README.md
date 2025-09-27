# 股票信息系统

基于Flask + tushare的A股实时数据展示系统，支持股票搜索、数据排序和价格图表展示。

## 功能特性

### 🕒 实时时间显示
- 页面顶部显示当前系统时间
- 每秒自动更新

### 🔍 股票搜索功能
- 支持股票代码和名称搜索
- 弹窗显示详细股票信息
- 实时搜索建议

### 📊 股票数据展示
- 显示A股市场所有股票信息
- 包含：序号、股票代码、股票名称、今日涨跌、股票价格、今日量比、当前市值、当前TTM
- 涨跌颜色显示：涨用红色，跌用绿色
- 每个字段支持排序功能

### 📈 股票详情图表
- 点击股票名称查看详情页面
- 显示近20个交易日价格走势图
- 使用Chart.js绘制交互式图表

### 🌓 主题切换
- 支持Light/Dark两种主题模式
- 主题设置自动保存到本地存储

### 📱 响应式设计
- 支持桌面和移动设备
- 自适应屏幕尺寸

## 技术栈

### 后端
- **Flask**: Web框架
- **tushare**: 股票数据API
- **pandas**: 数据处理
- **flask-cors**: 跨域支持

### 前端
- **HTML5**: 页面结构
- **CSS3**: 样式和主题
- **JavaScript**: 交互功能
- **Chart.js**: 图表绘制
- **Font Awesome**: 图标库

### 字体设置
- **英文**: Cascadia Code（等宽字体）
- **中文**: 微软雅黑

## 安装和运行

### 1. 环境要求
- Python 3.7+
- pip

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 运行项目
```bash
python run.py
```

或者直接运行：
```bash
python app.py
```

### 4. 访问网站
打开浏览器访问：[http://localhost:5000](http://localhost:5000)

## 项目结构

```
stock_website/
├── app.py                 # Flask主应用
├── run.py                 # 启动脚本
├── requirements.txt       # 依赖包列表
├── README.md             # 项目说明
├── static/               # 静态文件
│   ├── css/
│   │   └── styles.css    # 样式文件
│   └── js/
│       ├── main.js       # 主页JavaScript
│       └── stock_detail.js # 股票详情页JavaScript
└── templates/            # HTML模板
    ├── index.html        # 主页模板
    └── stock_detail.html # 股票详情页模板
```

## API接口

### 获取所有股票数据
```
GET /api/stocks
```

### 搜索股票
```
GET /api/search_stock/<keyword>
```

### 获取股票历史数据
```
GET /api/stock_history/<ts_code>
```

## 配置说明

### tushare API Token
项目中已配置了tushare API token，如需更换请修改 `app.py` 中的 `TUSHARE_TOKEN` 变量。

### 主题配置
系统默认为Light主题，用户可通过右上角按钮切换到Dark主题，设置会自动保存。

## 浏览器兼容性

- Chrome 60+
- Firefox 55+
- Safari 12+
- Edge 79+

## 注意事项

1. **API限制**: tushare API有调用频率限制，首次加载可能较慢
2. **数据延迟**: 股票数据可能有延迟，仅供参考
3. **网络依赖**: 需要稳定的网络连接来获取股票数据

## 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **端口被占用**
   - 修改 `app.py` 中的端口号
   - 或终止占用5000端口的进程

3. **数据加载失败**
   - 检查网络连接
   - 验证tushare API token是否有效

4. **图表不显示**
   - 确保网络连接正常（Chart.js从CDN加载）
   - 检查浏览器控制台是否有JavaScript错误

## 开发说明

### 自定义主题
修改 `static/css/styles.css` 中的CSS变量来自定义主题颜色。

### 添加新功能
1. 后端API：在 `app.py` 中添加新的路由
2. 前端功能：在对应的JavaScript文件中添加功能
3. 样式：在 `styles.css` 中添加样式

## 许可证

本项目仅供学习和研究使用，不得用于商业用途。

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue到项目仓库
- 发送邮件到开发者邮箱

---

**免责声明**: 本系统提供的股票数据仅供参考，不构成投资建议。投资有风险，入市需谨慎。