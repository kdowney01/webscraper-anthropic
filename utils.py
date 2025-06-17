"""Utility functions for the web scraper."""

import os
import re
import hashlib
import filetype
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
from typing import Optional, Tuple, Set
import validators
import logging

logger = logging.getLogger(__name__)


def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    try:
        return validators.url(url) is True
    except Exception:
        return False


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize and resolve URL."""
    if not url:
        return ""
    
    # Join with base URL if relative
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # Parse and reconstruct to normalize
    parsed = urlparse(url)
    
    # Remove fragment (anchor)
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    if parsed.query:
        normalized += f"?{parsed.query}"
    
    return normalized


def get_domain(url: str) -> str:
    """Extract domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except Exception:
        return ""


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for filesystem compatibility."""
    if not filename:
        return "unnamed"
    
    # Remove or replace invalid characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    filename = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Truncate if too long, preserving extension
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext
    
    return filename or "unnamed"


def get_file_extension_from_url(url: str) -> str:
    """Extract file extension from URL."""
    try:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        _, ext = os.path.splitext(path)
        return ext.lower()
    except Exception:
        return ""


def get_content_type_from_extension(extension: str) -> str:
    """Determine content type from file extension."""
    ext = extension.lower().lstrip('.')
    
    image_exts = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'tiff', 'ico'}
    video_exts = {'mp4', 'webm', 'avi', 'mov', 'mkv', 'wmv', 'flv', '3gp', 'ogv'}
    
    if ext in image_exts:
        return "image"
    elif ext in video_exts:
        return "video"
    else:
        return "other"


def detect_file_type(file_path: str) -> Optional[str]:
    """Detect file type using python-magic."""
    try:
        kind = filetype.guess(file_path)
        if kind is None:
            return None
        return kind.extension
    except Exception as e:
        logger.warning(f"Could not detect file type for {file_path}: {e}")
        return None


def generate_unique_filename(directory: Path, base_name: str, extension: str = "") -> str:
    """Generate unique filename in directory to avoid conflicts."""
    if not extension.startswith('.') and extension:
        extension = f".{extension}"
    
    original_name = f"{base_name}{extension}"
    file_path = directory / original_name
    
    if not file_path.exists():
        return original_name
    
    # Generate numbered variants
    counter = 1
    while True:
        name_with_counter = f"{base_name}_{counter}{extension}"
        file_path = directory / name_with_counter
        if not file_path.exists():
            return name_with_counter
        counter += 1
        
        # Safety check to avoid infinite loop
        if counter > 9999:
            # Use hash-based name as fallback
            hash_suffix = hashlib.md5(original_name.encode()).hexdigest()[:8]
            return f"{base_name}_{hash_suffix}{extension}"


def create_directory(path: Path) -> bool:
    """Create directory if it doesn't exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def get_file_hash(file_path: Path) -> str:
    """Calculate MD5 hash of file for duplicate detection."""
    try:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return ""


def is_duplicate_file(file_path: Path, existing_files: Set[str]) -> bool:
    """Check if file is duplicate based on hash."""
    if not file_path.exists():
        return False
    
    file_hash = get_file_hash(file_path)
    return file_hash in existing_files


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    return f"{size:.1f} {units[unit_index]}"


def extract_filename_from_url(url: str) -> str:
    """Extract filename from URL."""
    try:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = os.path.basename(path)
        
        if not filename or filename == '/':
            # Generate filename from domain if path is empty
            domain = get_domain(url)
            filename = f"{domain}_page"
        
        return sanitize_filename(filename)
    except Exception:
        return "unknown_file"


def get_robots_txt_url(url: str) -> str:
    """Get robots.txt URL for given domain."""
    try:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    except Exception:
        return ""


def is_external_link(url: str, base_domain: str) -> bool:
    """Check if URL is external to base domain."""
    try:
        url_domain = get_domain(url)
        return url_domain != base_domain.lower()
    except Exception:
        return True


def extract_links_from_text(text: str, base_url: str = "") -> Set[str]:
    """Extract URLs from text content."""
    url_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    )
    
    links = set()
    for match in url_pattern.finditer(text):
        url = match.group()
        normalized_url = normalize_url(url, base_url)
        if is_valid_url(normalized_url):
            links.add(normalized_url)
    
    return links


def should_respect_robots_txt(url: str, user_agent: str = "*") -> Tuple[bool, str]:
    """Check if URL should be crawled according to robots.txt."""
    try:
        import urllib.robotparser
        
        robots_url = get_robots_txt_url(url)
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        
        can_fetch = rp.can_fetch(user_agent, url)
        delay = rp.crawl_delay(user_agent) or 0
        
        return can_fetch, str(delay)
    except Exception as e:
        logger.warning(f"Could not check robots.txt for {url}: {e}")
        return True, "0"  # Default to allowing crawl if can't check


def clean_text_content(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def is_likely_content_url(url: str) -> bool:
    """Heuristic to determine if URL likely contains downloadable content."""
    # Skip common non-content URLs
    skip_patterns = [
        r'/api/',
        r'/ajax/',
        r'\.json$',
        r'\.xml$',
        r'\.css$',
        r'\.js$',
        r'/search\?',
        r'/login',
        r'/logout',
        r'/admin',
    ]
    
    for pattern in skip_patterns:
        if re.search(pattern, url, re.IGNORECASE):
            return False
    
    return True