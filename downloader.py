"""Content downloader with progress tracking and error handling."""

import os
import time
import logging
from pathlib import Path
from typing import Optional, Dict, Set, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

from .config import Config
from .utils import (
    sanitize_filename, extract_filename_from_url, get_file_extension_from_url,
    get_content_type_from_extension, generate_unique_filename, create_directory,
    get_file_hash, format_file_size, normalize_url
)

logger = logging.getLogger(__name__)


@dataclass
class DownloadResult:
    """Result of a download operation."""
    url: str
    success: bool
    file_path: Optional[Path] = None
    error: Optional[str] = None
    file_size: int = 0
    content_type: str = ""
    skipped: bool = False
    skip_reason: str = ""


class ContentDownloader:
    """Downloads content from URLs with progress tracking."""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = self._create_session()
        self.downloaded_hashes: Set[str] = set()
        self.stats = {
            'total_files': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_files': 0,
            'total_bytes': 0
        }
    
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
    
    def download_file(self, url: str, output_dir: Path, 
                     filename: Optional[str] = None,
                     progress_callback: Optional[Callable] = None) -> DownloadResult:
        """Download a single file."""
        try:
            # Normalize URL
            url = normalize_url(url)
            
            # Determine filename
            if not filename:
                filename = extract_filename_from_url(url)
            
            # Get file extension and content type
            extension = get_file_extension_from_url(url)
            content_type = get_content_type_from_extension(extension)
            
            # Check if content type should be downloaded
            if not self.config.should_download_content_type(content_type):
                return DownloadResult(
                    url=url, success=False, skipped=True,
                    skip_reason=f"Content type '{content_type}' not enabled"
                )
            
            # Create output directory
            final_output_dir = self.config.get_content_path(output_dir, content_type)
            if not create_directory(final_output_dir):
                return DownloadResult(
                    url=url, success=False,
                    error=f"Failed to create output directory: {final_output_dir}"
                )
            
            # Generate unique filename
            base_name = sanitize_filename(os.path.splitext(filename)[0])
            unique_filename = generate_unique_filename(final_output_dir, base_name, extension)
            file_path = final_output_dir / unique_filename
            
            # Check file size before downloading
            try:
                head_response = self.session.head(url, timeout=30)
                content_length = head_response.headers.get('content-length')
                
                if content_length:
                    file_size = int(content_length)
                    size_limit = self.config.get_size_limit(content_type)
                    
                    if size_limit > 0 and file_size > size_limit:
                        return DownloadResult(
                            url=url, success=False, skipped=True,
                            skip_reason=f"File too large: {format_file_size(file_size)} "
                                       f"(limit: {format_file_size(size_limit)})"
                        )
            except Exception as e:
                logger.warning(f"Could not check file size for {url}: {e}")
            
            # Download file
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get actual content length
            content_length = response.headers.get('content-length')
            total_size = int(content_length) if content_length else 0
            
            # Check size limit again with actual size
            if total_size > 0:
                size_limit = self.config.get_size_limit(content_type)
                if size_limit > 0 and total_size > size_limit:
                    return DownloadResult(
                        url=url, success=False, skipped=True,
                        skip_reason=f"File too large: {format_file_size(total_size)}"
                    )
            
            # Download with progress tracking
            downloaded_size = 0
            chunk_size = 8192
            
            with open(file_path, 'wb') as f:
                if progress_callback and total_size > 0:
                    progress_bar = tqdm(
                        total=total_size, unit='B', unit_scale=True,
                        desc=f"Downloading {unique_filename}"
                    )
                
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress_bar.update(len(chunk))
                
                if progress_callback and total_size > 0:
                    progress_bar.close()
            
            # Check for duplicates
            file_hash = get_file_hash(file_path)
            if file_hash in self.downloaded_hashes:
                os.remove(file_path)
                return DownloadResult(
                    url=url, success=False, skipped=True,
                    skip_reason="Duplicate file (same content)"
                )
            
            self.downloaded_hashes.add(file_hash)
            
            # Update stats
            self.stats['successful_downloads'] += 1
            self.stats['total_bytes'] += downloaded_size
            
            logger.info(f"Downloaded: {url} -> {file_path}")
            
            return DownloadResult(
                url=url, success=True, file_path=file_path,
                file_size=downloaded_size, content_type=content_type
            )
            
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP error: {str(e)}"
            logger.error(f"Failed to download {url}: {error_msg}")
            
            self.stats['failed_downloads'] += 1
            
            return DownloadResult(url=url, success=False, error=error_msg)
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Failed to download {url}: {error_msg}")
            
            self.stats['failed_downloads'] += 1
            
            return DownloadResult(url=url, success=False, error=error_msg)
    
    def download_multiple(self, urls: list, output_dir: Path,
                         progress_callback: Optional[Callable] = None) -> Dict[str, DownloadResult]:
        """Download multiple files concurrently."""
        results = {}
        self.stats['total_files'] = len(urls)
        
        if not urls:
            return results
        
        logger.info(f"Starting download of {len(urls)} files with {self.config.max_workers} workers")
        
        with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
            # Submit all download tasks
            future_to_url = {}
            for url in urls:
                future = executor.submit(self.download_file, url, output_dir, None, progress_callback)
                future_to_url[future] = url
                
                # Rate limiting
                if self.config.delay_between_requests > 0:
                    time.sleep(self.config.delay_between_requests)
            
            # Collect results
            if progress_callback:
                progress_bar = tqdm(total=len(urls), desc="Overall Progress")
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    results[url] = result
                    
                    if result.skipped:
                        self.stats['skipped_files'] += 1
                        logger.info(f"Skipped {url}: {result.skip_reason}")
                    
                except Exception as e:
                    error_msg = f"Task execution error: {str(e)}"
                    results[url] = DownloadResult(url=url, success=False, error=error_msg)
                    self.stats['failed_downloads'] += 1
                    logger.error(f"Task failed for {url}: {error_msg}")
                
                if progress_callback:
                    progress_bar.update(1)
            
            if progress_callback:
                progress_bar.close()
        
        self._log_summary()
        return results
    
    def download_text_content(self, url: str, content: str, output_dir: Path,
                             filename: Optional[str] = None) -> DownloadResult:
        """Save text content to file."""
        try:
            if not self.config.download_text:
                return DownloadResult(
                    url=url, success=False, skipped=True,
                    skip_reason="Text content download not enabled"
                )
            
            # Determine filename
            if not filename:
                filename = extract_filename_from_url(url) + ".txt"
            elif not filename.endswith('.txt'):
                filename += '.txt'
            
            # Create output directory
            final_output_dir = self.config.get_content_path(output_dir, "text")
            if not create_directory(final_output_dir):
                return DownloadResult(
                    url=url, success=False,
                    error=f"Failed to create output directory: {final_output_dir}"
                )
            
            # Generate unique filename
            base_name = sanitize_filename(os.path.splitext(filename)[0])
            unique_filename = generate_unique_filename(final_output_dir, base_name, ".txt")
            file_path = final_output_dir / unique_filename
            
            # Write content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            file_size = os.path.getsize(file_path)
            
            # Update stats
            self.stats['successful_downloads'] += 1
            self.stats['total_bytes'] += file_size
            
            logger.info(f"Saved text content: {url} -> {file_path}")
            
            return DownloadResult(
                url=url, success=True, file_path=file_path,
                file_size=file_size, content_type="text"
            )
            
        except Exception as e:
            error_msg = f"Failed to save text content: {str(e)}"
            logger.error(f"Failed to save text for {url}: {error_msg}")
            
            self.stats['failed_downloads'] += 1
            
            return DownloadResult(url=url, success=False, error=error_msg)
    
    def get_stats(self) -> Dict[str, any]:
        """Get download statistics."""
        return self.stats.copy()
    
    def _log_summary(self) -> None:
        """Log download summary."""
        logger.info("Download Summary:")
        logger.info(f"  Total files: {self.stats['total_files']}")
        logger.info(f"  Successful: {self.stats['successful_downloads']}")
        logger.info(f"  Failed: {self.stats['failed_downloads']}")
        logger.info(f"  Skipped: {self.stats['skipped_files']}")
        logger.info(f"  Total size: {format_file_size(self.stats['total_bytes'])}")
    
    def cleanup(self) -> None:
        """Clean up resources."""
        if self.session:
            self.session.close()