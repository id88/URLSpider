#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
工具函数模块
"""

import re
import time
import random
import string
from typing import List, Set, Tuple, Optional, Any
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode

# 导入 colorama
try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
except ImportError:
    # 如果 colorama 不可用，创建虚拟类
    class DummyColor:
        def __getattr__(self, name):
            return ""
    
    Fore = DummyColor()
    Back = DummyColor()
    Style = DummyColor()
    
    def init(**kwargs):
        pass

# 初始化colorama
init(autoreset=True)

class URLNormalizer:
    """URL规范化工具类"""
    
    @staticmethod
    def normalize(url: str, base_url: str = None) -> str:
        """
        规范化URL
        :param url: 原始URL
        :param base_url: 基础URL
        :return: 规范化后的URL
        """
        if not url or url.strip() == "":
            return ""
        
        # 去除两端的空白和引号
        url = url.strip().strip('"').strip("'")
        
        # 黑名单检查
        black_keywords = ['javascript:', 'mailto:', 'tel:', 'data:', 'blob:', 'about:']
        if any(url.lower().startswith(keyword) for keyword in black_keywords):
            return ""
        
        # 如果没有 base_url,只处理完整 URL
        if not base_url:
            if url.startswith(('http://', 'https://', 'ftp://')):
                return URLNormalizer._normalize_components(url)
            return ""
        
        # 使用 urljoin 正确处理相对路径
        # urljoin 会自动处理各种相对路径情况:
        # - 绝对路径: /path -> http://domain/path
        # - 相对路径: path -> http://domain/base/path
        # - 上级路径: ../path -> http://domain/path
        # - 协议相对: //domain/path -> http://domain/path
        try:
            absolute_url = urljoin(base_url, url)
            return URLNormalizer._normalize_components(absolute_url)
        except Exception:
            return ""
    
    @staticmethod
    def _normalize_components(url: str) -> str:
        """规范化URL组件"""
        try:
            parsed = urlparse(url)
            
            # 统一为小写的协议和域名
            scheme = parsed.scheme.lower()
            netloc = parsed.netloc.lower()
            
            # 移除默认端口
            if ':' in netloc:
                host, port = netloc.split(':', 1)
                if (scheme == 'http' and port == '80') or (scheme == 'https' and port == '443'):
                    netloc = host
            
            # 规范化路径
            path = parsed.path
            if not path:
                path = '/'
            
            # 移除路径中的./和../
            path_parts = []
            for part in path.split('/'):
                if part == '.':
                    continue
                elif part == '..':
                    if path_parts:
                        path_parts.pop()
                else:
                    path_parts.append(part)
            path = '/'.join(path_parts)
            
            # 保留原始查询参数,不进行过度规范化
            query = parsed.query
            
            # 重建URL
            normalized = urlunparse((
                scheme,
                netloc,
                path,
                parsed.params,
                query,
                ''  # 移除fragment
            ))
            
            return normalized
            
        except Exception as e:
            # 如果规范化失败,返回空字符串而不是原始URL
            return ""
    
    @staticmethod
    def get_domain(url: str) -> str:
        """提取域名"""
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except:
            return ""
    
    @staticmethod
    def get_base_domain(url: str) -> str:
        """提取主域名（二级域名）"""
        domain = URLNormalizer.get_domain(url)
        if not domain:
            return ""
        
        parts = domain.split('.')
        if len(parts) > 2:
            # 处理类似 .co.uk 的特殊情况
            if domain.endswith('.co.uk') or domain.endswith('.com.cn'):
                return '.'.join(parts[-3:])
            return '.'.join(parts[-2:])
        return domain
    
    @staticmethod
    def is_same_domain(url1: str, url2: str) -> bool:
        """判断是否同一域名"""
        domain1 = URLNormalizer.get_base_domain(url1)
        domain2 = URLNormalizer.get_base_domain(url2)
        return domain1 and domain2 and domain1 == domain2


class ProgressBar:
    """进度条工具类"""
    
    def __init__(self, total: int, desc: str = "Processing"):
        self.total = total
        self.desc = desc
        self.current = 0
        self.start_time = time.time()
        self.bar_length = 40
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
        return False
    
    def update(self, n: int = 1):
        """更新进度"""
        self.current += n
        self._display()
    
    def _display(self):
        """显示进度条"""
        percent = self.current / self.total * 100
        filled_length = int(self.bar_length * self.current // self.total)
        
        bar = '█' * filled_length + '░' * (self.bar_length - filled_length)
        
        elapsed_time = time.time() - self.start_time
        if self.current > 0:
            items_per_second = self.current / elapsed_time
            eta = (self.total - self.current) / items_per_second if items_per_second > 0 else 0
            time_info = f"{elapsed_time:.1f}s, {items_per_second:.1f}it/s, ETA: {eta:.1f}s"
        else:
            time_info = ""
        
        print(f"\r{Fore.CYAN}{self.desc}:{Fore.RESET} |{bar}| {percent:6.2f}% ({self.current}/{self.total}) {time_info}", end="", flush=True)
    
    def close(self):
        """结束进度条"""
        print()


def generate_random_user_agent() -> str:
    """生成随机User-Agent"""
    from config import USER_AGENTS
    return random.choice(USER_AGENTS)


def is_valid_url(url: str) -> bool:
    """验证URL是否有效"""
    if not url or url.strip() == "":
        return False
    
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except:
        return False


def print_color(text: str, color: str = Fore.WHITE, style: str = Style.NORMAL) -> None:
    """彩色打印"""
    print(f"{style}{color}{text}{Style.RESET_ALL}")


def print_success(text: str) -> None:
    """打印成功信息"""
    print_color(f"[+] {text}", Fore.GREEN)


def print_error(text: str) -> None:
    """打印错误信息"""
    print_color(f"[-] {text}", Fore.RED)


def print_warning(text: str) -> None:
    """打印警告信息"""
    print_color(f"[!] {text}", Fore.YELLOW)


def print_info(text: str) -> None:
    """打印信息"""
    print_color(f"[*] {text}", Fore.CYAN)