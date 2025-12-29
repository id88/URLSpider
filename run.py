#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
URLSpider 运行入口
直接运行此文件: python run.py
"""

import sys
import os

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main

if __name__ == "__main__":
    main()