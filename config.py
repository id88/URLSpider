#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
URLSpider 配置文件
"""

import re
from typing import List, Pattern

# 用户代理配置
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
]

# URL提取正则表达式
URL_PATTERNS: List[Pattern] = [
    # 完整URL (http, https, ftp, ws, wss)
    re.compile(r'(?:https?|ftp|ws|wss)://[a-zA-Z0-9][a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=%]*', re.IGNORECASE),
    
    # 相对URL (//开头)
    re.compile(r'//[a-zA-Z0-9][a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=%]*', re.IGNORECASE),
    
    # 标签属性 (src, href)
    re.compile(r'(?:src|href|data-src|data-href)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    
    # JavaScript动态URL（fetch / axios / XMLHttpRequest）
    re.compile(r'(?:fetch|axios\.get|axios\.post|\.ajax|\.get|\.post|XMLHttpRequest)\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
    
    # GraphQL 端点（包括 /graphql 或 /api/graphql 等相对路径）
    re.compile(r'["\'](/?(?:api/)?graphql[^"\']*)["\']', re.IGNORECASE),
    
    # Service Worker 注册地址
    re.compile(r'navigator\.serviceWorker\.register\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
    
    # URL函数参数
    re.compile(r'(?:url|URL|endpoint|api|path)\s*[:=]\s*["\']([^"\']+)["\']', re.IGNORECASE),
    
    # 页面跳转
    re.compile(r'(?:window\.location|location\.href|\.src)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE),
    
    # WebSocket连接
    re.compile(r'new\s+WebSocket\s*\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
    
    # 相对路径文件
    re.compile(r'["\'][./][^"\']+\.(?:js|css|png|jpg|jpeg|gif|svg|ico|php|asp|aspx|jsp|json|html|xml|txt|csv)[^"\']*["\']', re.IGNORECASE),
]

# 黑名单模式
BLACKLIST_PATTERNS = [
    re.compile(r'^javascript:', re.IGNORECASE),
    re.compile(r'^mailto:', re.IGNORECASE),
    re.compile(r'^tel:', re.IGNORECASE),
    re.compile(r'^#', re.IGNORECASE),
    re.compile(r'^data:', re.IGNORECASE),
    re.compile(r'^blob:', re.IGNORECASE),
    re.compile(r'^about:', re.IGNORECASE),
]

# 文件扩展名白名单
ALLOWED_EXTENSIONS = {
    '.woff', '.woff2', '.ttf', '.eot'
}

# 请求配置
REQUEST_CONFIG = {
    'timeout': 10,
    'verify': False,
    'allow_redirects': True,
    'max_retries': 3,
    'retry_delay': 1,
    'max_workers': 5,  # 线程池大小
    'max_depth': 3,    # 最大爬取深度
    'max_urls_per_page': 100,  # 每页最大URL数量
}

# 输出配置
OUTPUT_CONFIG = {
    'color_output': True,
    'show_progress': True,
    'group_by_type': True,
    'limit_display': 50,  # 控制台显示限制
    'save_full_results': True,
}