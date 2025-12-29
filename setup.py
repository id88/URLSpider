from setuptools import setup, find_packages
import os

setup(
    name="urlspider",
    version="2.0.0",
    py_modules=["main", "config", "utils", "filter", "extractor", "crawler", "output"],
    install_requires=[
        "requests>=2.25.0",
        "beautifulsoup4>=4.9.0",
        "colorama>=0.4.4",
        "tldextract>=3.1.0",
    ],
    entry_points={
        "console_scripts": [
            "urlspider=main:main",
        ],
    },
    author="id88",
    description="快速从网站中提取URL和子域名的工具",
    long_description=open("README.md", encoding="utf-8").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    python_requires=">=3.6",
)