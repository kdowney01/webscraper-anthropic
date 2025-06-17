"""Core web scraper logic with BeautifulSoup."""

import time
import logging
from pathlib import Path
from typing import List, Set, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config
from .downloader import ContentDownloader, DownloadResult
from .utils import (
    is_valid_url, normalize_url, get_domain, is_external_link,
    should_respect_robots_txt, clean_text_content, is_likely_content_url
)

logger = logging.getLogger(__name__)


class WebScraper:
    """Main web scraper class."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = self._create_session()
        self.downloader = ContentDownloader(config)
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, Tuple[bool, float]] = {}
    
    def _create_session(self) -> requests.Session:
        """Create configured requests session."""
        session = requests.Session()
        
        # Set user agent
        session.headers.update({'User-Agent': self.config.user_agent})
        
        # Configure retries
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _check_robots_txt(self, url: str) -> Tuple[bool, float]:
        """Check robots.txt compliance for URL."""
        if not self.config.respect_robots_txt:
            return True, 0.0
        
        domain = get_domain(url)
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        try:
            can_fetch, delay_str = should_respect_robots_txt(url, self.config.user_agent)
            delay = float(delay_str) if delay_str else 0.0
            
            self.robots_cache[domain] = (can_fetch, delay)
            return can_fetch, delay
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {domain}: {e}")
            # Default to allowing access if can't check
            self.robots_cache[domain] = (True, 0.0)
            return True, 0.0
    
    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a web page."""
        try:
            # Check robots.txt
            can_fetch, robots_delay = self._check_robots_txt(url)
            if not can_fetch:
                logger.info(f"Skipping {url} due to robots.txt restrictions")
                return None
            
            # Apply robots.txt delay
            if robots_delay > 0:
                time.sleep(robots_delay)
            
            # Apply configured delay
            if self.config.delay_between_requests > 0:
                time.sleep(self.config.delay_between_requests)
            
            logger.info(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'lxml')
            return soup
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> Set[str]:
        """Extract all links from page."""
        links = set()
        
        # Extract from anchor tags
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            if href:
                absolute_url = urljoin(base_url, href)
                normalized_url = normalize_url(absolute_url)
                if is_valid_url(normalized_url) and is_likely_content_url(normalized_url):
                    links.add(normalized_url)
        
        return links
    
    def _extract_media_urls(self, soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
        """Extract media URLs from page."""
        media_urls = {
            'images': [],
            'videos': []
        }
        
        # Extract images
        if self.config.download_images:
            for img_tag in soup.find_all('img', src=True):
                src = img_tag.get('src')
                if src:
                    absolute_url = urljoin(base_url, src)
                    normalized_url = normalize_url(absolute_url)
                    if is_valid_url(normalized_url):
                        media_urls['images'].append(normalized_url)
            
            # Also check for srcset attributes
            for img_tag in soup.find_all('img', srcset=True):
                srcset = img_tag.get('srcset')
                if srcset:
                    # Parse srcset (simplified - just extract URLs)
                    for src_entry in srcset.split(','):
                        src = src_entry.strip().split()[0]
                        absolute_url = urljoin(base_url, src)
                        normalized_url = normalize_url(absolute_url)
                        if is_valid_url(normalized_url):
                            media_urls['images'].append(normalized_url)
        
        # Extract videos
        if self.config.download_videos:
            # Video tags
            for video_tag in soup.find_all('video'):
                src = video_tag.get('src')
                if src:
                    absolute_url = urljoin(base_url, src)
                    normalized_url = normalize_url(absolute_url)
                    if is_valid_url(normalized_url):
                        media_urls['videos'].append(normalized_url)
                
                # Source tags within video
                for source_tag in video_tag.find_all('source', src=True):
                    src = source_tag.get('src')
                    if src:
                        absolute_url = urljoin(base_url, src)
                        normalized_url = normalize_url(absolute_url)
                        if is_valid_url(normalized_url):
                            media_urls['videos'].append(normalized_url)
        
        # Remove duplicates
        media_urls['images'] = list(set(media_urls['images']))
        media_urls['videos'] = list(set(media_urls['videos']))
        
        return media_urls
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from page."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean text
        return clean_text_content(text)
    
    def _should_follow_link(self, url: str, base_domain: str, current_depth: int) -> bool:
        """Determine if link should be followed."""
        # Check depth limit
        if current_depth >= self.config.max_depth:
            return False
        
        # Check if already visited
        if url in self.visited_urls:
            return False
        
        # Check external links
        if is_external_link(url, base_domain) and not self.config.follow_external_links:
            return False
        
        return True
    
    def scrape_url(self, url: str, depth: int = 0) -> Dict[str, any]:
        """Scrape a single URL."""
        results = {
            'url': url,
            'success': False,
            'text_content': '',
            'media_urls': {'images': [], 'videos': []},
            'links': set(),
            'download_results': {},
            'error': None
        }
        
        try:
            # Normalize URL
            url = normalize_url(url)
            
            # Check if already visited
            if url in self.visited_urls:
                results['error'] = "URL already visited"
                return results
            
            # Mark as visited
            self.visited_urls.add(url)
            
            # Fetch page
            soup = self._fetch_page(url)
            if not soup:
                results['error'] = "Failed to fetch page"
                return results
            
            # Extract content
            results['text_content'] = self._extract_text_content(soup)
            results['media_urls'] = self._extract_media_urls(soup, url)
            results['links'] = self._extract_links(soup, url)
            results['success'] = True
            
            return results
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            results['error'] = str(e)
            return results
    
    def scrape_and_download(self, url: str, output_dir: Optional[Path] = None,
                           max_depth: Optional[int] = None) -> Dict[str, any]:
        """Scrape URL and download all content."""
        if max_depth is None:
            max_depth = self.config.max_depth
        
        if output_dir is None:
            domain = get_domain(url)
            output_dir = self.config.get_output_path(domain)
        
        results = {
            'scraped_urls': {},
            'download_results': {},
            'stats': {
                'total_urls_scraped': 0,
                'successful_scrapes': 0,
                'failed_scrapes': 0,
                'total_media_found': 0,
                'download_stats': {}
            }
        }
        
        # Queue for BFS crawling
        url_queue = [(normalize_url(url), 0)]  # (url, depth)
        base_domain = get_domain(url)
        
        logger.info(f"Starting scrape of {url} with max depth {max_depth}")
        
        while url_queue:
            current_url, depth = url_queue.pop(0)
            
            # Scrape current URL
            scrape_result = self.scrape_url(current_url, depth)
            results['scraped_urls'][current_url] = scrape_result
            results['stats']['total_urls_scraped'] += 1
            
            if scrape_result['success']:
                results['stats']['successful_scrapes'] += 1
                
                # Save text content if enabled
                if self.config.download_text and scrape_result['text_content']:
                    text_result = self.downloader.download_text_content(
                        current_url, scrape_result['text_content'], output_dir
                    )
                    results['download_results'][f"{current_url}_text"] = text_result
                
                # Collect media URLs for download
                all_media_urls = []
                all_media_urls.extend(scrape_result['media_urls']['images'])
                all_media_urls.extend(scrape_result['media_urls']['videos'])
                
                results['stats']['total_media_found'] += len(all_media_urls)
                
                # Download media files
                if all_media_urls:
                    logger.info(f"Found {len(all_media_urls)} media files on {current_url}")
                    download_results = self.downloader.download_multiple(
                        all_media_urls, output_dir, progress_callback=True
                    )
                    results['download_results'].update(download_results)
                
                # Add links to queue for deeper crawling
                if depth < max_depth:
                    for link in scrape_result['links']:
                        if self._should_follow_link(link, base_domain, depth + 1):
                            url_queue.append((link, depth + 1))
            
            else:
                results['stats']['failed_scrapes'] += 1
                logger.warning(f"Failed to scrape {current_url}: {scrape_result.get('error', 'Unknown error')}")
        
        # Get download statistics
        results['stats']['download_stats'] = self.downloader.get_stats()
        
        logger.info("Scraping completed")
        self._log_scrape_summary(results['stats'])
        
        return results
    
    def scrape_multiple_urls(self, urls: List[str], output_dir: Optional[Path] = None) -> Dict[str, any]:
        """Scrape multiple URLs."""
        all_results = {
            'results': {},
            'combined_stats': {
                'total_urls': len(urls),
                'successful_scrapes': 0,
                'failed_scrapes': 0,
                'total_media_found': 0,
                'total_downloads': 0
            }
        }
        
        for url in urls:
            logger.info(f"Processing URL: {url}")
            
            # Determine output directory
            if output_dir is None:
                domain = get_domain(url)
                url_output_dir = self.config.get_output_path(domain)
            else:
                url_output_dir = output_dir
            
            # Scrape and download
            result = self.scrape_and_download(url, url_output_dir)
            all_results['results'][url] = result
            
            # Update combined stats
            stats = result['stats']
            all_results['combined_stats']['successful_scrapes'] += stats['successful_scrapes']
            all_results['combined_stats']['failed_scrapes'] += stats['failed_scrapes']
            all_results['combined_stats']['total_media_found'] += stats['total_media_found']
            all_results['combined_stats']['total_downloads'] += stats['download_stats'].get('successful_downloads', 0)
        
        logger.info("Multiple URL scraping completed")
        self._log_combined_summary(all_results['combined_stats'])
        
        return all_results
    
    def _log_scrape_summary(self, stats: Dict[str, any]) -> None:
        """Log scraping summary."""
        logger.info("Scraping Summary:")
        logger.info(f"  URLs scraped: {stats['total_urls_scraped']}")
        logger.info(f"  Successful: {stats['successful_scrapes']}")
        logger.info(f"  Failed: {stats['failed_scrapes']}")
        logger.info(f"  Media files found: {stats['total_media_found']}")
        
        download_stats = stats.get('download_stats', {})
        if download_stats:
            logger.info(f"  Files downloaded: {download_stats.get('successful_downloads', 0)}")
            logger.info(f"  Download failures: {download_stats.get('failed_downloads', 0)}")
            logger.info(f"  Files skipped: {download_stats.get('skipped_files', 0)}")
    
    def _log_combined_summary(self, stats: Dict[str, any]) -> None:
        """Log combined scraping summary."""
        logger.info("Combined Scraping Summary:")
        logger.info(f"  Total URLs processed: {stats['total_urls']}")
        logger.info(f"  Successful scrapes: {stats['successful_scrapes']}")
        logger.info(f"  Failed scrapes: {stats['failed_scrapes']}")
        logger.info(f"  Total media found: {stats['total_media_found']}")
        logger.info(f"  Total downloads: {stats['total_downloads']}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            self.session.close()
        if self.downloader:
            self.downloader.cleanup()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()