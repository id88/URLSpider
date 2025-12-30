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
    # re.compile(r"""
    #   (?:"|')                               # Start newline delimiter
    #   (
    #     ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
    #     [^"'/]{1,}\.                        # Match a domainname (any character + dot)
    #     [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
    #     |
    #     ((?:/|\.\./ |\./)                    # Start with /,../,./
    #     [^"'><,;| *()(%%$^/\\[\]]          # Next character can't be...
    #     [^"'><,;|()]{1,})                   # Rest of the characters can't be
    #     |
    #     ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
    #     [a-zA-Z0-9_\-/]{1,}                 # Resource name
    #     \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
    #     (?:[\?|/][^"|']{0,}|))              # ? mark with parameters
    #     |
    #     ([a-zA-Z0-9_\-]{1,}                 # filename
    #     \.(?:php|asp|aspx|jsp|json|
    #          action|html|js|txt|xml)             # . + extension
    #     (?:\?[^"|']{0,}|))                  # ? mark with parameters
    #   )
    #   (?:"|')                               # End newline delimiter
    # """, re.VERBOSE),

    re.compile(r"""
    (?:"|')(((?:[a-zA-Z]{1,10}://|//)[^"'/]{1,}\.[a-zA-Z]{2,}[^"']{0,})|((?:/|\.\./|\./)[^"'><,;|*()(%%$^/\\[\]][^"'><,;|()]{1,})|([a-zA-Z0-9_\-/]{1,}/[a-zA-Z0-9_\-/]{1,}\.(?:[a-zA-Z]{1,6}|action|config|env|htaccess|yml|yaml|ts|tsx|vue|svelte|md|py|rb|go|java|cs|swift|kt|scala|pl|sh|bat|cmd)(?:[?|#][^"|']{0,}|))|([a-zA-Z0-9_\-]{1,}\.(?:php|php3|php4|php5|php7|php8|phtml|phar|asp|aspx|ascx|ashx|asmx|jsp|jspx|do|action|json|jsonp|xml|html|htm|xhtml|js|jsx|mjs|cjs|ts|tsx|css|scss|sass|less|txt|text|log|md|rst|pdf|doc|docx|xls|xlsx|ppt|pptx|zip|rar|7z|gz|tar|svg|png|jpg|jpeg|gif|bmp|ico|webp|mp3|mp4|avi|mov|flv|wmv|mkv|env|config|ini|cfg|conf|properties|yml|yaml|toml|sql|db|sqlite|mdb|dbf|pgsql|mysql|bak|backup|old|tmp|temp|swp|swo|py|pyc|pyo|pyd|rb|erb|go|java|class|jar|cs|csproj|vb|vbs|swift|pl|pm|sh|bash|bat|cmd|ps1|psm1|vbs|reg|dll|exe|msi|app|apk|ipa|deb|rpm|pkg)(?:[?|#][^"|']{0,}|)))(?:"|')
    """, re.VERBOSE),
    
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
    re.compile(r'^data:', re.IGNORECASE),  # 过滤 data: 协议 (base64等)
    re.compile(r'^blob:', re.IGNORECASE),
    re.compile(r'^about:', re.IGNORECASE),
    # 新增过滤规则
    re.compile(r'^(true|false|null|undefined)$', re.IGNORECASE),  # 布尔值和 null
    re.compile(r'^(webkit|moz|ms|o)-?', re.IGNORECASE),  # CSS 前缀和浏览器关键词
    re.compile(r'^[\d\s\u4e00-\u9fa5%]+$'),  # 纯数字、空格、中文、百分号
    re.compile(r'^(width|height|initial-scale|maximum-scale|minimum-scale|user-scalable)', re.IGNORECASE),  # meta viewport 属性
    re.compile(r'^[\u4e00-\u9fa5]'),  # 以中文开头的字符串
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