"""Setup script for webscraper package."""

from setuptools import setup, find_packages

setup(
    name="web-scraper",
    version="0.1.0",
    description="A Python application for scraping web content including text, images, and videos",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "lxml>=4.9.0",
        "urllib3>=2.0.0", 
        "validators>=0.20.0",
        "filetype>=1.2.0",
        "tqdm>=4.65.0",
        "click>=8.1.0",
        "rich>=13.0.0",
        "pyyaml>=6.0",
        "colorlog>=6.7.0",
    ],
    entry_points={
        "console_scripts": [
            "webscraper=webscraper_src.cli:main",
        ],
    },
    python_requires=">=3.8",
    author="Kyle Downey",
    author_email="kdowney01@example.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers", 
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)