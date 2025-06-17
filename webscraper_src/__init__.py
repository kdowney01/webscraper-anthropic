"""
Web Scraper - A Python application for scraping web content.

This package provides functionality to scrape text, images, and videos
from websites and organize them in local directory structures.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .scraper import WebScraper
from .config import Config
from .downloader import ContentDownloader

__all__ = ["WebScraper", "Config", "ContentDownloader"]