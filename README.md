
## 安装

### 方法1：直接使用
```bash
# 安装依赖
pip install -r requirements.txt

# 直接运行
python run.py -u https://example.com
```

### 方法2：安装为系统命令
```bash
pip install -e .

# 然后可以直接使用
urlspider -u https://example.com
```

## 使用方法

### 基本用法
```bash
# 扫描单个网站
python run.py -u https://example.com

# 深度爬取
python run.py -u https://example.com --deep --depth 2

# 处理文件中的URL
python run.py -f urls.txt

# 专门提取JS文件中的URL
python run.py -u https://example.com -j
```

### 高级选项
```bash
# 使用多线程（默认5线程）
python run.py -u https://example.com --threads 10

# 设置超时和重试
python run.py -u https://example.com --timeout 15 --retries 5

# 导出为JSON和CSV
python run.py -u https://example.com --json --csv

# 使用过滤器
python run.py -u https://example.com --filter "api" --exclude "logout"

# 包含外部域名
python run.py -u https://example.com --include-external

# 自定义输出目录
python run.py -u https://example.com -o ./my_results
```

### 参数说明
```
输入选项:
  -u, --url URL         目标网站URL
  -f, --file FILE       包含URL或JS的文件路径
  -c, --cookie COOKIE   网站Cookie
  --user-agent AGENT    自定义User-Agent

提取选项:
  -j, --js              专门提取JS文件中的URL
  -d, --deep            深度爬取（递归爬取链接）
  --depth DEPTH         深度爬取的最大深度（默认：3）
  --max-pages PAGES     最大爬取页面数（默认：100）
  --include-external    包含外部域名
  --filter PATTERN      URL过滤模式（正则表达式）
  --exclude PATTERN     URL排除模式（正则表达式）

输出选项:
  -o, --output DIR      输出目录（默认：results）
  --json                导出为JSON格式
  --csv                 导出为CSV格式
  --no-color            禁用彩色输出
  --quiet               安静模式，减少输出
  --no-progress         禁用进度条

性能选项:
  --threads THREADS     线程数（默认：5）
  --timeout TIMEOUT     请求超时时间（秒，默认：10）
  --retries RETRIES     最大重试次数（默认：3）
```

## 输出示例

程序会输出：
1. 结果摘要（找到的URL和子域名数量）
2. 分类结果（按文件类型分类）
3. 统计信息（URL类型统计）
4. 结果文件保存在`results`目录中

## 优化特性

1. **模块化设计**：代码结构清晰，易于维护和扩展
2. **增强的正则表达式**：支持更多URL格式和JavaScript动态URL
3. **智能URL过滤**：支持黑白名单、域名过滤、文件类型过滤
4. **性能优化**：支持多线程并发处理、连接池、智能缓存
5. **URL规范化**：自动处理相对路径、协议、端口等
6. **丰富的输出格式**：支持彩色输出、分类显示、统计信息、多种导出格式
7. **进度显示**：实时显示处理进度和预估时间

## 最终目录结构
```
urlspider/
├── run.py              # 新的主入口文件
├── main.py             # 修改后的主程序
├── config.py           # 配置文件
├── extractor.py        # URL提取模块
├── crawler.py          # 爬虫模块
├── filter.py           # 过滤模块
├── utils.py            # 工具模块
├── output.py           # 输出模块
├── __init__.py         # 包初始化
├── requirements.txt    # 依赖文件
├── setup.py            # 安装脚本（可选）
└── README.md           # 使用说明
```

## 使用方式

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行程序
```bash
# 方式1：使用 run.py
python run.py -u https://example.com

# 方式2：直接运行 main.py
python main.py -u https://example.com

# 方式3：如果安装了 setup.py
urlspider -u https://example.com
```

