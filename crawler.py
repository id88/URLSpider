#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
网页抓取模块
"""

import requests
import time
import random
from typing import Optional, Dict, Any, List, Set, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from config import REQUEST_CONFIG
from utils import generate_random_user_agent, print_error, print_warning, ProgressBar
from extractor import URLExtractor

# 禁用SSL警告
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class WebCrawler:
    """网页爬虫"""
    
    def __init__(self, 
                 timeout: int = None,
                 max_retries: int = None,
                 max_workers: int = None,
                 headers: Dict[str, str] = None,
                 cookies: Dict[str, str] = None):
        """
        初始化爬虫
        :param timeout: 请求超时时间
        :param max_retries: 最大重试次数
        :param max_workers: 线程池大小
        :param headers: 自定义请求头
        :param cookies: Cookies
        """
        self.timeout = timeout or REQUEST_CONFIG['timeout']
        self.max_retries = max_retries or REQUEST_CONFIG['max_retries']
        self.max_workers = max_workers or REQUEST_CONFIG['max_workers']
        
        # 请求会话
        self.session = requests.Session()
        
        # 配置请求头
        self.headers = headers or {
            'User-Agent': generate_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # 配置Cookies
        if cookies:
            self.session.cookies.update(cookies)
        
        # 配置重试机制
        adapter = HTTPAdapter(
            max_retries=self.max_retries,
            pool_connections=10,
            pool_maxsize=10
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        
        # 访问过的URL缓存
        self.visited_urls: Set[str] = set()
        
        # 提取器
        self.extractor = None
    
    def set_extractor(self, extractor: URLExtractor):
        """设置URL提取器"""
        self.extractor = extractor
    
    def fetch(self, url: str, method: str = 'GET', **kwargs) -> Optional[str]:
        """
        获取网页内容
        :param url: 目标URL
        :param method: HTTP方法
        :param kwargs: 其他请求参数
        :return: 网页内容或None
        """
        if url in self.visited_urls:
            return None
        
        try:
            # 随机延迟，避免被封
            time.sleep(random.uniform(0.1, 0.5))
            
            # 发送请求
            response = self.session.request(
                method=method,
                url=url,
                headers=self.headers,
                timeout=self.timeout,
                verify=False,
                allow_redirects=True,
                **kwargs
            )
            
            response.raise_for_status()
            
            # 更新User-Agent
            self.headers['User-Agent'] = generate_random_user_agent()
            
            # 缓存访问过的URL
            self.visited_urls.add(url)
            
            # 返回内容
            return response.content.decode('utf-8', errors='ignore')
            
        except requests.exceptions.Timeout:
            print_error(f"Timeout fetching {url}")
        except requests.exceptions.HTTPError as e:
            print_error(f"HTTP error fetching {url}: {e}")
        except requests.exceptions.ConnectionError:
            print_error(f"Connection error fetching {url}")
        except requests.exceptions.RequestException as e:
            print_error(f"Error fetching {url}: {e}")
        except Exception as e:
            print_error(f"Unexpected error fetching {url}: {e}")
        
        return None
    
    def crawl_page(self, url: str, extract_js: bool = False) -> Tuple[List[str], List[str]]:
        """
        爬取单个页面并提取URL
        :param url: 目标URL
        :param extract_js: 是否专门提取JS文件中的URL
        :return: (页面URL列表, 子域名列表)
        """
        if not self.extractor:
            print_error("Extractor not set!")
            return [], []
        
        print(f"\nCrawling: {url}")
        
        # 获取页面内容
        content = self.fetch(url)
        if not content:
            return [], []
        
        # 提取URL
        page_urls = self.extractor.extract_from_html(content, url)
        
        # 如果启用了JS提取，也爬取JS文件
        if extract_js:
            js_urls = [url for url in page_urls if url.endswith('.js')]
            for js_url in js_urls[:5]:  # 限制JS文件数量
                js_content = self.fetch(js_url)
                if js_content:
                    js_extracted = self.extractor.extract_from_js(js_content, js_url)
                    page_urls.extend(js_extracted)
        
        return page_urls, []
    
    def crawl_deep(self, 
                   start_url: str, 
                   max_depth: int = None,
                   max_pages: int = 100,
                   extract_js: bool = False) -> Tuple[List[str], List[str]]:
        """
        深度爬取
        :param start_url: 起始URL
        :param max_depth: 最大爬取深度
        :param max_pages: 最大页面数
        :param extract_js: 是否提取JS文件
        :return: (URL列表, 子域名列表)
        """
        if not self.extractor:
            print_error("Extractor not set!")
            return [], []
        
        max_depth = max_depth or REQUEST_CONFIG['max_depth']
        
        all_urls = set()
        all_subdomains = set()
        
        # 待爬取队列: (url, depth)
        queue = [(start_url, 0)]
        processed = 0
        
        print(f"\nStarting deep crawl from {start_url}")
        print(f"Max depth: {max_depth}, Max pages: {max_pages}")
        
        with ProgressBar(max_pages, "Crawling pages") as progress:
            while queue and processed < max_pages:
                current_url, depth = queue.pop(0)
                
                # 检查是否已访问
                if current_url in self.visited_urls:
                    continue
                
                # 爬取页面
                page_urls, _ = self.crawl_page(current_url, extract_js)
                
                # 添加到结果
                all_urls.update(page_urls)
                
                # 如果未达到最大深度，将新URL加入队列
                if depth < max_depth:
                    for new_url in page_urls:
                        # 只添加同域名的页面链接
                        if self.extractor.filter.filter(new_url):
                            queue.append((new_url, depth + 1))
                
                processed += 1
                progress.update(1)
                
                # 随机延迟
                time.sleep(random.uniform(0.2, 1.0))
        
        print(f"\nCrawled {processed} pages, found {len(all_urls)} URLs")
        
        # 提取子域名
        if all_urls and self.extractor.domain:
            from extractor import SubdomainExtractor
            subdomain_extractor = SubdomainExtractor(self.extractor.domain)
            all_subdomains = subdomain_extractor.extract_from_urls(list(all_urls))
        
        return list(all_urls), list(all_subdomains)
    
    def crawl_batch(self, 
                    urls: List[str], 
                    extract_js: bool = False,
                    show_progress: bool = True) -> Tuple[List[str], List[str]]:
        """
        批量爬取URL
        :param urls: URL列表
        :param extract_js: 是否提取JS文件
        :param show_progress: 是否显示进度条
        :return: (URL列表, 子域名列表)
        """
        if not self.extractor:
            print_error("Extractor not set!")
            return [], []
        
        all_urls = set()
        all_subdomains = set()
        
        def process_url(url):
            try:
                page_urls, _ = self.crawl_page(url, extract_js)
                return page_urls
            except Exception as e:
                print_error(f"Error processing {url}: {e}")
                return []
        
        # 使用线程池并发处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            if show_progress:
                with ProgressBar(len(urls), "Processing URLs") as progress:
                    futures = {executor.submit(process_url, url): url for url in urls}
                    
                    for future in as_completed(futures):
                        try:
                            page_urls = future.result()
                            all_urls.update(page_urls)
                        except Exception as e:
                            url = futures[future]
                            print_error(f"Error processing {url}: {e}")
                        
                        progress.update(1)
            else:
                futures = [executor.submit(process_url, url) for url in urls]
                for future in as_completed(futures):
                    try:
                        page_urls = future.result()
                        all_urls.update(page_urls)
                    except Exception as e:
                        print_error(f"Error in thread: {e}")
        
        return list(all_urls), list(all_subdomains)
    
    def clear_visited(self):
        """清除访问记录"""
        self.visited_urls.clear()
    
    def get_visited_count(self) -> int:
        """获取已访问的URL数量"""
        return len(self.visited_urls)