#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
URLSpider - 快速从网站中提取URL和子域名的工具
优化版本
"""

import argparse
import sys
import os
from typing import List, Optional

# 直接导入本地模块
import config
from utils import (
    print_color, print_success, print_error, print_warning, print_info,
    Fore, Style, is_valid_url, URLNormalizer
)
from filter import URLFilter
from extractor import URLExtractor, SubdomainExtractor
from crawler import WebCrawler
from output import ResultExporter, ResultPrinter


class URLSpider:
    """URLSpider 主类"""
    
    def __init__(self):
        self.args = None
        self.crawler = None
        self.extractor = None
        self.filter = None
        self.exporter = ResultExporter()
    
    def parse_args(self):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            description='URLSpider - 从网站中快速提取URL和子域名',
            epilog='\nExamples:\n'
                  '  python run.py -u https://example.com\n'
                  '  python run.py -u https://example.com --deep\n'
                  '  python run.py -f urls.txt --js\n'
                  '  python run.py -u https://example.com --threads 10 --json'
        )
        
        # 输入选项
        input_group = parser.add_argument_group('Input Options')
        input_group.add_argument('-u', '--url', 
                                help='目标网站URL (e.g., https://example.com)')
        input_group.add_argument('-f', '--file', 
                                help='包含URL或JS的文件路径')
        input_group.add_argument('-c', '--cookie', 
                                help='网站Cookie (e.g., "session=abc123; token=xyz")')
        input_group.add_argument('--user-agent', 
                                help='自定义User-Agent')
        
        # 提取选项
        extract_group = parser.add_argument_group('Extraction Options')
        extract_group.add_argument('-j', '--js', 
                                  action='store_true',
                                  help='专门提取JS文件中的URL')
        extract_group.add_argument('-d', '--deep', 
                                  action='store_true',
                                  help='深度爬取（递归爬取链接）')
        extract_group.add_argument('--depth', 
                                  type=int, 
                                  default=config.REQUEST_CONFIG['max_depth'],
                                  help=f'深度爬取的最大深度（默认：{config.REQUEST_CONFIG["max_depth"]}）')
        extract_group.add_argument('--max-pages', 
                                  type=int, 
                                  default=100,
                                  help='最大爬取页面数（默认：100）')
        extract_group.add_argument('--include-external', 
                                  action='store_true',
                                  help='包含外部域名')
        extract_group.add_argument('--filter', 
                                  help='URL过滤模式（正则表达式）')
        extract_group.add_argument('--exclude', 
                                  help='URL排除模式（正则表达式）')
        
        # 输出选项
        output_group = parser.add_argument_group('Output Options')
        output_group.add_argument('-o', '--output', 
                                 help='输出目录（默认：results）')
        output_group.add_argument('--json', 
                                 action='store_true',
                                 help='导出为JSON格式')
        output_group.add_argument('--csv', 
                                 action='store_true',
                                 help='导出为CSV格式')
        output_group.add_argument('--no-color', 
                                 action='store_true',
                                 help='禁用彩色输出')
        output_group.add_argument('--quiet', 
                                 action='store_true',
                                 help='安静模式，减少输出')
        output_group.add_argument('--no-progress', 
                                 action='store_true',
                                 help='禁用进度条')
        
        # 性能选项
        perf_group = parser.add_argument_group('Performance Options')
        perf_group.add_argument('--threads', 
                               type=int, 
                               default=config.REQUEST_CONFIG['max_workers'],
                               help=f'线程数（默认：{config.REQUEST_CONFIG["max_workers"]}）')
        perf_group.add_argument('--timeout', 
                               type=int, 
                               default=config.REQUEST_CONFIG['timeout'],
                               help=f'请求超时时间（秒，默认：{config.REQUEST_CONFIG["timeout"]}）')
        perf_group.add_argument('--retries', 
                               type=int, 
                               default=config.REQUEST_CONFIG['max_retries'],
                               help=f'最大重试次数（默认：{config.REQUEST_CONFIG["max_retries"]}）')
        
        self.args = parser.parse_args()
        
        # 验证参数
        self._validate_args()
        
        return self.args
    
    def _validate_args(self):
        """验证参数"""
        # 检查必须参数
        if not self.args.url and not self.args.file:
            print_error("必须指定URL(-u)或文件(-f)")
            sys.exit(1)
        
        # 验证URL格式
        if self.args.url:
            if not is_valid_url(self.args.url):
                # 尝试添加协议
                if not self.args.url.startswith(('http://', 'https://')):
                    self.args.url = f'https://{self.args.url}'
                    if not is_valid_url(self.args.url):
                        print_error(f"无效的URL: {self.args.url}")
                        sys.exit(1)
        
        # 验证文件路径
        if self.args.file:
            if not os.path.exists(self.args.file):
                print_error(f"文件不存在: {self.args.file}")
                sys.exit(1)
        
        # 验证数值参数
        if self.args.depth < 1:
            print_error("深度必须大于0")
            sys.exit(1)
        
        if self.args.max_pages < 1:
            print_error("最大页面数必须大于0")
            sys.exit(1)
        
        if self.args.threads < 1:
            print_error("线程数必须大于0")
            sys.exit(1)
        
        if self.args.timeout < 1:
            print_error("超时时间必须大于0")
            sys.exit(1)
        
        if self.args.retries < 0:
            print_error("重试次数不能为负数")
            sys.exit(1)
        
        # 设置输出目录
        if self.args.output:
            self.exporter.output_dir = self.args.output
            os.makedirs(self.args.output, exist_ok=True)
        
        # 禁用彩色输出
        if self.args.no_color:
            global Fore, Style
            Fore = type('Fore', (), {k: '' for k in dir(Fore) if not k.startswith('_')})()
            Style = type('Style', (), {k: '' for k in dir(Style) if not k.startswith('_')})()
    
    def initialize(self):
        """初始化组件"""
        if not self.args.quiet:
            print_color("\n" + "="*60, Fore.CYAN, Style.BRIGHT)
            print_color("URLSpider - URL & Subdomain Extractor", Fore.CYAN, Style.BRIGHT)
            print_color("="*60, Fore.CYAN, Style.BRIGHT)
        
        # 构建过滤规则
        exclude_patterns = []
        if self.args.exclude:
            exclude_patterns.append(self.args.exclude)
        
        include_patterns = []
        if self.args.filter:
            include_patterns.append(self.args.filter)
        
        # 初始化过滤器
        self.filter = URLFilter(
            domain=self.args.url if self.args.url else None,
            include_subdomains=not self.args.include_external,
            exclude_patterns=exclude_patterns,
            include_patterns=include_patterns
        )
        
        # 初始化提取器
        self.extractor = URLExtractor(
            domain=self.args.url if self.args.url else None,
            filter_rules=self.filter
        )
        
        # 构建请求头
        headers = {'User-Agent': config.USER_AGENTS[0]}
        if self.args.user_agent:
            headers['User-Agent'] = self.args.user_agent
        
        # 构建Cookies
        cookies = {}
        if self.args.cookie:
            for cookie_pair in self.args.cookie.split(';'):
                cookie_pair = cookie_pair.strip()
                if '=' in cookie_pair:
                    key, value = cookie_pair.split('=', 1)
                    cookies[key] = value
        
        # 初始化爬虫
        self.crawler = WebCrawler(
            timeout=self.args.timeout,
            max_retries=self.args.retries,
            max_workers=self.args.threads,
            headers=headers,
            cookies=cookies
        )
        self.crawler.set_extractor(self.extractor)
        
        if not self.args.quiet:
            print_info(f"目标: {self.args.url or self.args.file}")
            if self.args.deep:
                print_info(f"深度爬取: 深度={self.args.depth}, 最大页面数={self.args.max_pages}")
            if self.args.js:
                print_info("启用JS文件专门提取")
            print_info(f"线程数: {self.args.threads}")
    
    def process_url(self) -> tuple:
        """处理单个URL"""
        if not self.args.quiet:
            print_info(f"开始处理URL: {self.args.url}")
        
        if self.args.deep:
            # 深度爬取
            urls, subdomains = self.crawler.crawl_deep(
                start_url=self.args.url,
                max_depth=self.args.depth,
                max_pages=self.args.max_pages,
                extract_js=self.args.js
            )
        else:
            # 普通爬取
            urls, _ = self.crawler.crawl_page(self.args.url, self.args.js)
            
            # 提取子域名
            if urls:
                subdomain_extractor = SubdomainExtractor(self.args.url)
                subdomains = list(subdomain_extractor.extract_from_urls(urls))
            else:
                subdomains = []
        
        return urls, subdomains
    
    def process_file(self) -> tuple:
        """处理文件"""
        if not self.args.quiet:
            print_info(f"开始处理文件: {self.args.file}")
        
        # 读取文件内容
        with open(self.args.file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        
        # 提取URL和子域名
        all_urls = []
        all_subdomains = []
        
        for line in lines:
            if not self.args.quiet:
                print_info(f"处理: {line}")
            
            if is_valid_url(line):
                # 如果是URL，爬取它
                original_url = self.args.url if hasattr(self.args, 'url') else None
                self.args.url = line
                
                # 临时初始化以处理这个URL
                temp_filter = URLFilter(
                    domain=line,
                    include_subdomains=not self.args.include_external,
                    exclude_patterns=[self.args.exclude] if self.args.exclude else [],
                    include_patterns=[self.args.filter] if self.args.filter else []
                )
                
                temp_extractor = URLExtractor(
                    domain=line,
                    filter_rules=temp_filter
                )
                
                temp_crawler = WebCrawler(
                    timeout=self.args.timeout,
                    max_retries=self.args.retries,
                    max_workers=min(self.args.threads, 2),  # 限制每个URL的线程数
                    headers={'User-Agent': config.USER_AGENTS[0]},
                    cookies={}
                )
                temp_crawler.set_extractor(temp_extractor)
                
                if self.args.deep:
                    urls, subdomains = temp_crawler.crawl_deep(
                        start_url=line,
                        max_depth=self.args.depth,
                        max_pages=self.args.max_pages // max(1, len(lines)),
                        extract_js=self.args.js
                    )
                else:
                    urls, _ = temp_crawler.crawl_page(line, self.args.js)
                    
                    # 提取子域名
                    if urls:
                        subdomain_extractor = SubdomainExtractor(line)
                        subdomains = list(subdomain_extractor.extract_from_urls(urls))
                    else:
                        subdomains = []
                
                all_urls.extend(urls)
                all_subdomains.extend(subdomains)
                
                # 恢复原始URL
                if original_url:
                    self.args.url = original_url
            else:
                # 假设是JS代码或文件路径
                try:
                    if os.path.exists(line):
                        # 是文件路径
                        with open(line, 'r', encoding='utf-8') as js_file:
                            content = js_file.read()
                    else:
                        # 是JS代码片段
                        content = line
                    
                    urls = self.extractor.extract_from_js(content, self.args.url if hasattr(self.args, 'url') else None)
                    all_urls.extend(urls)
                except Exception as e:
                    if not self.args.quiet:
                        print_warning(f"处理 '{line}' 时出错: {e}")
        
        # 去重
        unique_urls = list(set(all_urls))
        unique_subdomains = list(set(all_subdomains))
        
        return unique_urls, unique_subdomains
    
    def run(self):
        """运行主程序"""
        # 解析参数
        self.parse_args()
        
        # 初始化
        self.initialize()
        
        # 处理输入
        if self.args.url:
            urls, subdomains = self.process_url()
        else:
            urls, subdomains = self.process_file()
        
        # 去重和排序
        urls = sorted(set(urls), key=lambda x: (URLNormalizer.get_domain(x) or '', x))
        subdomains = sorted(set(subdomains))
        
        # 输出结果
        if not self.args.quiet:
            ResultPrinter.print_summary(urls, subdomains, self.args.url if self.args.url else None)
            ResultPrinter.print_categorized(urls, self.args.url if self.args.url else None)
            ResultPrinter.print_statistics(urls, self.args.url if self.args.url else None)
        
        # 导出结果
        if urls or subdomains:
            # 文本导出
            self.exporter.export_text(urls, subdomains)
            
            # JSON导出
            if self.args.json:
                data = {
                    'target': self.args.url or self.args.file,
                    'timestamp': self.exporter.timestamp,
                    'urls': urls,
                    'subdomains': subdomains,
                    'statistics': {
                        'total_urls': len(urls),
                        'total_subdomains': len(subdomains),
                        'unique_domains': len(set(URLNormalizer.get_domain(url) for url in urls if URLNormalizer.get_domain(url))),
                    }
                }
                self.exporter.export_json(data)
            
            # CSV导出
            if self.args.csv and urls:
                self.exporter.export_csv(urls)
        
        if not self.args.quiet:
            print_success(f"处理完成！共找到 {len(urls)} 个URL 和 {len(subdomains)} 个子域名")
            print_info(f"结果保存在目录: {self.exporter.output_dir}")


def main():
    """主函数"""
    try:
        finder = URLSpider()
        finder.run()
    except KeyboardInterrupt:
        print_error("\n用户中断")
        sys.exit(1)
    except Exception as e:
        print_error(f"程序错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()