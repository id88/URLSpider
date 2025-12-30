#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
URL过滤模块
"""

import re
from typing import List, Set, Pattern, Optional
from urllib.parse import urlparse

from config import BLACKLIST_PATTERNS, ALLOWED_EXTENSIONS
from utils import URLNormalizer


class URLFilter:
    """URL过滤器"""
    
    def __init__(self, 
                 domain: Optional[str] = None,
                 include_subdomains: bool = True,
                 exclude_patterns: List[str] = None,
                 include_patterns: List[str] = None):
        """
        初始化过滤器
        :param domain: 目标域名
        :param include_subdomains: 是否包含子域名
        :param exclude_patterns: 排除模式列表
        :param include_patterns: 包含模式列表
        """
        self.domain = domain
        self.include_subdomains = include_subdomains
        self.base_domain = URLNormalizer.get_base_domain(domain) if domain else None
        
        # 编译排除模式
        self.exclude_patterns: List[Pattern] = BLACKLIST_PATTERNS.copy()
        if exclude_patterns:
            for pattern in exclude_patterns:
                self.exclude_patterns.append(re.compile(pattern, re.IGNORECASE))
        
        # 编译包含模式
        self.include_patterns: List[Pattern] = []
        if include_patterns:
            for pattern in include_patterns:
                self.include_patterns.append(re.compile(pattern, re.IGNORECASE))
    
    def filter(self, url: str) -> bool:
        """
        过滤URL
        :param url: 待过滤的URL
        :return: True表示通过过滤，False表示被过滤
        """
        # 基本验证
        if not url or url.strip() == "":
            return False
        
        url = url.strip()
        
        # URL 格式有效性检查
        if not self._is_valid_url_format(url):
            return False
        
        # 规范化URL
        normalized_url = URLNormalizer.normalize(url, self.domain)
        if not normalized_url:
            return False
        
        # 检查黑名单模式
        for pattern in self.exclude_patterns:
            if pattern.search(normalized_url):
                return False
        
        # 域名过滤
        if self.domain:
            parsed = urlparse(normalized_url)
            url_domain = parsed.netloc.lower()
            
            if not url_domain:
                # 相对URL，默认通过
                pass
            elif self.include_subdomains:
                # 包含子域名
                if not self._is_subdomain(url_domain, self.base_domain):
                    # 检查是否在包含模式中
                    if not self._matches_include_patterns(normalized_url):
                        return False
            else:
                # 仅包含主域名
                if URLNormalizer.get_base_domain(url_domain) != self.base_domain:
                    # 检查是否在包含模式中
                    if not self._matches_include_patterns(normalized_url):
                        return False
        
        # 检查包含模式
        if self.include_patterns and not self._matches_include_patterns(normalized_url):
            return False
        
        return True
    
    def _is_valid_url_format(self, url: str) -> bool:
        """检查 URL 格式是否有效"""
        # 排除过短的 URL
        if len(url) < 3:
            return False
        
        # 排除只包含特殊字符的 URL
        if re.match(r'^[^a-zA-Z0-9/]+$', url):
            return False
        
        # 必须包含至少一个字母或数字
        if not re.search(r'[a-zA-Z0-9]', url):
            return False
        
        # 检查是否为有效的 URL 格式
        # 完整 URL 或相对路径
        if not (url.startswith(('http://', 'https://', 'ftp://', '//', '/')) or 
                re.match(r'^[a-zA-Z0-9_\-]+\.[a-zA-Z]{2,}', url)):
            # 检查是否为相对路径文件
            if not re.match(r'^\.{0,2}/?[a-zA-Z0-9_\-/]+\.[a-zA-Z]{1,10}', url):
                return False
        
        return True
    
    def _is_subdomain(self, url_domain: str, base_domain: str) -> bool:
        """判断是否为子域名"""
        if not url_domain or not base_domain:
            return False
        
        return url_domain == base_domain or url_domain.endswith('.' + base_domain)
    
    def _matches_include_patterns(self, url: str) -> bool:
        """检查是否匹配包含模式"""
        if not self.include_patterns:
            return False
        
        for pattern in self.include_patterns:
            if pattern.search(url):
                return True
        
        return False
    
    def filter_batch(self, urls: List[str]) -> List[str]:
        """批量过滤URL"""
        filtered = []
        for url in urls:
            if self.filter(url):
                filtered.append(url)
        return filtered
    
    def categorize_urls(self, urls: List[str]) -> dict:
        """
        分类URL
        :return: 分类后的URL字典
        """
        categories = {
            'internal': [],      # 内部URL
            'subdomains': [],    # 子域名
            'external': [],      # 外部URL
            'files': [],         # 文件资源
            'apis': [],          # API接口
            'static': [],        # 静态资源
        }
        
        if not self.domain:
            return categories
        
        for url in urls:
            normalized = URLNormalizer.normalize(url, self.domain)
            parsed = urlparse(normalized)
            
            # 检查文件类型
            path = parsed.path.lower()
            if any(path.endswith(ext) for ext in ['.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2']):
                categories['static'].append(normalized)
            elif any(path.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
                categories['files'].append(normalized)
            elif '/api/' in path or path.endswith(('.json', '.xml')):
                categories['apis'].append(normalized)
            
            # 检查域名
            url_domain = parsed.netloc.lower()
            if not url_domain:
                categories['internal'].append(normalized)
            elif url_domain == URLNormalizer.get_domain(self.domain):
                categories['internal'].append(normalized)
            elif URLNormalizer.get_base_domain(url_domain) == self.base_domain:
                categories['subdomains'].append(normalized)
            else:
                categories['external'].append(normalized)
        
        return categories