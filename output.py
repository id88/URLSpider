#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
输出格式化模块
"""

import json
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

from utils import (
    print_color, print_success, print_error, print_warning, print_info,
    Fore, Back, Style, URLNormalizer
)
from filter import URLFilter


class ResultExporter:
    """结果导出器"""
    
    def __init__(self, output_dir: str = "results"):
        """
        初始化导出器
        :param output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 时间戳用于生成文件名
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def export_text(self, 
                   urls: List[str], 
                   subdomains: List[str],
                   filename: Optional[str] = None) -> Dict[str, str]:
        """
        导出为文本文件
        :param urls: URL列表
        :param subdomains: 子域名列表
        :param filename: 文件名（不包含扩展名）
        :return: 文件路径字典
        """
        if not filename:
            filename = f"urlspider_results_{self.timestamp}"
        
        file_paths = {}
        
        # 导出URL
        if urls:
            url_file = os.path.join(self.output_dir, f"{filename}_urls.txt")
            with open(url_file, 'w', encoding='utf-8') as f:
                for url in sorted(urls):
                    f.write(f"{url}\n")
            file_paths['urls'] = url_file
            print_success(f"Exported {len(urls)} URLs to: {url_file}")
        
        # 导出子域名
        if subdomains:
            subdomain_file = os.path.join(self.output_dir, f"{filename}_subdomains.txt")
            with open(subdomain_file, 'w', encoding='utf-8') as f:
                for subdomain in sorted(subdomains):
                    f.write(f"{subdomain}\n")
            file_paths['subdomains'] = subdomain_file
            print_success(f"Exported {len(subdomains)} subdomains to: {subdomain_file}")
        
        return file_paths
    
    def export_json(self, 
                   data: Dict[str, Any],
                   filename: Optional[str] = None) -> str:
        """
        导出为JSON文件
        :param data: 要导出的数据
        :param filename: 文件名（不包含扩展名）
        :return: 文件路径
        """
        if not filename:
            filename = f"urlspider_results_{self.timestamp}"
        
        json_file = os.path.join(self.output_dir, f"{filename}.json")
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print_success(f"Exported results to JSON: {json_file}")
        return json_file
    
    def export_csv(self, 
                  urls: List[str],
                  filename: Optional[str] = None) -> str:
        """
        导出为CSV文件
        :param urls: URL列表
        :param filename: 文件名（不包含扩展名）
        :return: 文件路径
        """
        if not filename:
            filename = f"urlspider_urls_{self.timestamp}"
        
        csv_file = os.path.join(self.output_dir, f"{filename}.csv")
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['URL', 'Scheme', 'Domain', 'Path', 'Parameters'])
            
            for url in sorted(urls):
                try:
                    parsed = URLNormalizer.normalize(url)
                    scheme = parsed.split('://')[0] if '://' in parsed else ''
                    domain = URLNormalizer.get_domain(parsed)
                    path = parsed.split(domain, 1)[1] if domain else parsed
                    
                    # 分割路径和参数
                    if '?' in path:
                        path_part, param_part = path.split('?', 1)
                        params = param_part
                    else:
                        path_part = path
                        params = ''
                    
                    writer.writerow([url, scheme, domain, path_part, params])
                except Exception as e:
                    writer.writerow([url, '', '', '', f'Error: {str(e)}'])
        
        print_success(f"Exported {len(urls)} URLs to CSV: {csv_file}")
        return csv_file


class ResultPrinter:
    """结果打印机"""
    
    @staticmethod
    def print_summary(urls: List[str], subdomains: List[str], domain: str = None):
        """打印结果摘要"""
        print("\n" + "="*60)
        print_color("RESULTS SUMMARY", Fore.GREEN, Style.BRIGHT)
        print("="*60)
        
        if domain:
            print_color(f"Target Domain: {domain}", Fore.CYAN)
        
        print(f"\n{Fore.YELLOW}URLs Found:{Fore.RESET} {len(urls)}")
        print(f"{Fore.YELLOW}Subdomains Found:{Fore.RESET} {len(subdomains)}")
        
        # 如果URL数量较多，只显示部分
        if urls and len(urls) > 50:
            print(f"\n{Fore.YELLOW}Displaying first 50 URLs:{Fore.RESET}")
            for i, url in enumerate(urls[:50], 1):
                print(f"  {i:3d}. {url}")
            print(f"  ... and {len(urls) - 50} more URLs")
        elif urls:
            print(f"\n{Fore.YELLOW}URLs:{Fore.RESET}")
            for i, url in enumerate(urls, 1):
                print(f"  {i:3d}. {url}")
        
        # 显示子域名
        if subdomains:
            print(f"\n{Fore.YELLOW}Subdomains:{Fore.RESET}")
            for i, subdomain in enumerate(sorted(subdomains), 1):
                print(f"  {i:3d}. {subdomain}")
        
        print("="*60)
    
    @staticmethod
    def print_categorized(urls: List[str], domain: str = None):
        """打印分类结果"""
        if not urls:
            return
        
        print("\n" + "="*60)
        print_color("CATEGORIZED RESULTS", Fore.GREEN, Style.BRIGHT)
        print("="*60)
        
        # 初始化分类
        categories = {
            'JavaScript': [],
            'CSS': [],
            'Images': [],
            'Documents': [],
            'APIs': [],
            'Pages': [],
            'Others': [],
        }
        
        # 分类URL
        for url in urls:
            url_lower = url.lower()
            
            if url_lower.endswith('.js'):
                categories['JavaScript'].append(url)
            elif url_lower.endswith('.css'):
                categories['CSS'].append(url)
            elif any(url_lower.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.webp']):
                categories['Images'].append(url)
            elif any(url_lower.endswith(ext) for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']):
                categories['Documents'].append(url)
            elif '/api/' in url_lower or any(url_lower.endswith(ext) for ext in ['.json', '.xml']):
                categories['APIs'].append(url)
            elif any(url_lower.endswith(ext) for ext in ['.html', '.htm', '.php', '.asp', '.aspx', '.jsp']):
                categories['Pages'].append(url)
            else:
                categories['Others'].append(url)
        
        # 打印分类结果
        for category, urls_in_category in categories.items():
            if urls_in_category:
                print(f"\n{Fore.CYAN}{category} ({len(urls_in_category)}):{Fore.RESET}")
                for url in urls_in_category[:10]:  # 每类最多显示10个
                    print(f"  • {url}")
                if len(urls_in_category) > 10:
                    print(f"  ... and {len(urls_in_category) - 10} more")
        
        print("="*60)
    
    @staticmethod
    def print_statistics(urls: List[str], domain: str = None):
        """打印统计信息"""
        if not urls:
            return
        
        print("\n" + "="*60)
        print_color("STATISTICS", Fore.GREEN, Style.BRIGHT)
        print("="*60)
        
        # 计算统计信息
        stats = {
            'Total URLs': len(urls),
            'Unique Domains': len(set(URLNormalizer.get_domain(url) for url in urls if URLNormalizer.get_domain(url))),
            'HTTP URLs': len([url for url in urls if url.startswith('http://')]),
            'HTTPS URLs': len([url for url in urls if url.startswith('https://')]),
            'JS Files': len([url for url in urls if url.lower().endswith('.js')]),
            'CSS Files': len([url for url in urls if url.lower().endswith('.css')]),
            'Image Files': len([url for url in urls if any(url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico'])]),
            'API Endpoints': len([url for url in urls if '/api/' in url.lower()]),
        }
        
        # 打印统计信息
        max_key_length = max(len(key) for key in stats.keys())
        for key, value in stats.items():
            padding = ' ' * (max_key_length - len(key))
            print(f"{Fore.YELLOW}{key}:{padding} {Fore.WHITE}{value}")
        
        # 打印最常见的路径
        if domain:
            base_domain = URLNormalizer.get_base_domain(domain)
            internal_urls = [url for url in urls if base_domain in url]
            
            if internal_urls:
                # 提取路径频率
                path_freq = {}
                for url in internal_urls:
                    parsed = URLNormalizer.normalize(url)
                    path = parsed.split(base_domain, 1)[1] if base_domain in parsed else parsed
                    if '?' in path:
                        path = path.split('?')[0]
                    if path not in path_freq:
                        path_freq[path] = 0
                    path_freq[path] += 1
                
                # 打印最常见的路径
                print(f"\n{Fore.CYAN}Most Common Paths:{Fore.RESET}")
                sorted_paths = sorted(path_freq.items(), key=lambda x: x[1], reverse=True)
                for path, freq in sorted_paths[:10]:
                    print(f"  {freq:3d} × {path}")
        
        print("="*60)