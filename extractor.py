#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
URL提取模块
"""

import re
from typing import List, Set, Tuple, Optional, Dict, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import tldextract

from config import URL_PATTERNS
from utils import URLNormalizer, print_info, print_warning
from filter import URLFilter


class URLExtractor:
    """URL提取器"""
    
    def __init__(self, domain: Optional[str] = None, filter_rules: Optional[URLFilter] = None):
        """
        初始化提取器
        :param domain: 目标域名
        :param filter_rules: URL过滤规则
        """
        self.domain = domain
        self.filter = filter_rules or URLFilter(domain)
        
        # 缓存已提取的URL，避免重复
        self._extracted_cache: Set[str] = set()
    
    def extract_from_html(self, html_content: str, base_url: str = None) -> List[str]:
        """
        从HTML内容提取URL
        :param html_content: HTML内容
        :param base_url: 基础URL（用于相对路径转换）
        :return: 提取到的URL列表
        """
        urls = set()
        
        try:
            # 使用正则表达式提取
            regex_urls = self._extract_with_regex(html_content, base_url)
            urls.update(regex_urls)
            
            # 使用BeautifulSoup提取
            soup_urls = self._extract_with_soup(html_content, base_url)
            urls.update(soup_urls)
            
            # 从JavaScript代码中提取
            js_urls = self._extract_from_javascript(html_content, base_url)
            urls.update(js_urls)
            
        except Exception as e:
            print_warning(f"Error extracting URLs from HTML: {e}")
        
        # 添加默认 favicon.ico (如果有 base_url)
        if base_url:
            from urllib.parse import urlparse
            parsed = urlparse(base_url)
            if parsed.scheme and parsed.netloc:
                favicon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
                urls.add(favicon_url)
        
        # 过滤URL
        filtered_urls = self.filter.filter_batch(list(urls))
        
        # 缓存处理
        new_urls = []
        for url in filtered_urls:
            normalized = URLNormalizer.normalize(url, base_url)
            if normalized and normalized not in self._extracted_cache:
                self._extracted_cache.add(normalized)
                new_urls.append(normalized)
        
        return new_urls
    
    def extract_from_js(self, js_content: str, base_url: str = None) -> List[str]:
        """
        从JavaScript内容提取URL
        :param js_content: JavaScript内容
        :param base_url: 基础URL
        :return: 提取到的URL列表
        """
        urls = set()
        
        try:
            # 使用正则表达式提取
            regex_urls = self._extract_with_regex(js_content, base_url)
            urls.update(regex_urls)
            
            # 提取特定格式的URL
            specific_patterns = [
                # Webpack模块
                re.compile(r'__webpack_require__\(\s*["\']([^"\']+)["\']', re.IGNORECASE),
                # import/export语句
                re.compile(r'(?:import|export|from|require)\s*["\']([^"\']+)["\']', re.IGNORECASE),
                # 模板字符串中的URL
                re.compile(r'`([^`]+\.(?:js|css|png|jpg|jpeg|gif|svg))`', re.IGNORECASE),
            ]
            
            for pattern in specific_patterns:
                matches = pattern.findall(js_content)
                for match in matches:
                    if isinstance(match, str):
                        urls.add(match)
            
        except Exception as e:
            print_warning(f"Error extracting URLs from JavaScript: {e}")
        
        # 过滤URL
        filtered_urls = self.filter.filter_batch(list(urls))
        
        # 缓存处理
        new_urls = []
        for url in filtered_urls:
            normalized = URLNormalizer.normalize(url, base_url)
            if normalized and normalized not in self._extracted_cache:
                self._extracted_cache.add(normalized)
                new_urls.append(normalized)
        
        return new_urls
    
    def _extract_with_regex(self, content: str, base_url: str = None) -> List[str]:
        """使用正则表达式提取URL"""
        urls = set()
        
        for pattern in URL_PATTERNS:
            matches = pattern.findall(content)
            for match in matches:
                if isinstance(match, str):
                    # 简单字符串匹配
                    url = match.strip().strip('"').strip("'")
                    if url:
                        urls.add(url)
                elif isinstance(match, tuple):
                    # 如果正则中有分组，取第一个非空分组
                    for group in match:
                        if isinstance(group, str) and group.strip():
                            url = group.strip().strip('"').strip("'")
                            if url:
                                urls.add(url)
                            break
        
        return list(urls)
    
    def _extract_with_soup(self, html_content: str, base_url: str = None) -> List[str]:
        """使用BeautifulSoup提取URL"""
        urls = set()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 提取各种标签的URL
            tags_to_extract = {
                'a': 'href',
                'img': ['src', 'data-src'],
                'script': 'src',
                'iframe': 'src',
                'form': 'action',
                'embed': 'src',
                'source': 'src',
                'track': 'src',
                'area': 'href',
                'base': 'href',
                'meta': ['content', 'url'],
            }
            
            for tag, attributes in tags_to_extract.items():
                elements = soup.find_all(tag)
                for element in elements:
                    if isinstance(attributes, list):
                        for attr in attributes:
                            url = element.get(attr)
                            if url:
                                urls.add(url)
                    else:
                        url = element.get(attributes)
                        if url:
                            urls.add(url)
            
            # 特别处理 link 标签 (CSS 和 favicon)
            link_tags = soup.find_all('link')
            for link in link_tags:
                href = link.get('href')
                if href:
                    # 提取所有 link 标签的 href
                    urls.add(href)
                    # 特别标记 CSS 和 favicon
                    rel = link.get('rel')
                    if rel:
                        rel_str = ' '.join(rel) if isinstance(rel, list) else str(rel)
                        # stylesheet, icon, shortcut icon 等都要提取
                        if any(keyword in rel_str.lower() for keyword in ['stylesheet', 'icon']):
                            urls.add(href)
            
            # 提取CSS背景图
            style_tags = soup.find_all('style')
            for style in style_tags:
                if style.string:
                    bg_pattern = re.compile(r'url\s*\(\s*["\']?([^"\')]+)["\']?\s*\)', re.IGNORECASE)
                    matches = bg_pattern.findall(style.string)
                    urls.update(matches)
            
            # 提取内联样式
            elements_with_style = soup.find_all(style=True)
            for element in elements_with_style:
                style = element['style']
                bg_pattern = re.compile(r'url\s*\(\s*["\']?([^"\')]+)["\']?\s*\)', re.IGNORECASE)
                matches = bg_pattern.findall(style)
                urls.update(matches)
            
        except Exception as e:
            print_warning(f"Error extracting URLs with BeautifulSoup: {e}")
        
        return list(urls)
    
    def _extract_from_javascript(self, content: str, base_url: str = None) -> List[str]:
        """从JavaScript代码中提取URL"""
        urls = set()
        
        try:
            # 提取JSON数据中的URL
            json_pattern = re.compile(r'"url"\s*:\s*["\']([^"\']+)["\']', re.IGNORECASE)
            urls.update(json_pattern.findall(content))
            
            # 提取变量中的URL
            var_pattern = re.compile(r'(?:const|let|var)\s+[a-zA-Z_$][a-zA-Z0-9_$]*\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
            urls.update(var_pattern.findall(content))
            
        except Exception as e:
            print_warning(f"Error extracting URLs from JavaScript code: {e}")
        
        return list(urls)
    
    def clear_cache(self):
        """清除缓存"""
        self._extracted_cache.clear()
    
    def get_extracted_count(self) -> int:
        """获取已提取的URL数量"""
        return len(self._extracted_cache)


class SubdomainExtractor:
    """子域名提取器"""
    
    def __init__(self, domain: str):
        self.domain = domain
        self.base_domain = URLNormalizer.get_base_domain(domain)
    
    def extract_from_urls(self, urls: List[str]) -> Set[str]:
        """
        从URL列表中提取子域名
        :param urls: URL列表
        :return: 子域名集合
        """
        subdomains = set()
        
        for url in urls:
            try:
                parsed = urlparse(url)
                url_domain = parsed.netloc.lower()
                
                if not url_domain:
                    continue
                
                # 提取主域名部分
                extracted = tldextract.extract(url_domain)
                domain_parts = [extracted.subdomain, extracted.domain, extracted.suffix]
                full_domain = '.'.join([part for part in domain_parts if part])
                
                # 检查是否为子域名
                if full_domain.endswith(self.base_domain) and full_domain != self.base_domain:
                    subdomains.add(full_domain)
                
            except Exception as e:
                print_warning(f"Error extracting subdomain from {url}: {e}")
        
        return subdomains
    
    def extract_from_content(self, content: str) -> Set[str]:
        """
        从内容中直接提取子域名
        :param content: 文本内容
        :return: 子域名集合
        """
        subdomains = set()
        
        try:
            # 匹配子域名模式
            pattern = r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.' + re.escape(self.base_domain)
            matches = re.findall(pattern, content, re.IGNORECASE)
            
            for match in matches:
                if match and match.endswith(self.base_domain) and match != self.base_domain:
                    subdomains.add(match.lower())
            
        except Exception as e:
            print_warning(f"Error extracting subdomains from content: {e}")
        
        return subdomains