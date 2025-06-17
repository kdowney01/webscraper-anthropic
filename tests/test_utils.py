"""Tests for utility functions."""

import os
import tempfile
import pytest
from pathlib import Path

from webscraper.utils import (
    is_valid_url, normalize_url, get_domain, sanitize_filename,
    get_file_extension_from_url, get_content_type_from_extension,
    generate_unique_filename, format_file_size, extract_filename_from_url,
    is_external_link, clean_text_content, is_likely_content_url
)


class TestUrlUtils:
    """Test URL utility functions."""
    
    def test_is_valid_url(self):
        """Test URL validation."""
        assert is_valid_url('https://example.com') is True
        assert is_valid_url('http://example.com') is True
        assert is_valid_url('https://example.com/path?query=1') is True
        assert is_valid_url('not-a-url') is False
        assert is_valid_url('') is False
        assert is_valid_url('ftp://example.com') is False  # Only HTTP/HTTPS
    
    def test_normalize_url(self):
        """Test URL normalization."""
        base_url = 'https://example.com/page'
        
        # Absolute URLs should remain unchanged
        assert normalize_url('https://other.com/path') == 'https://other.com/path'
        
        # Relative URLs should be resolved
        assert normalize_url('/relative', base_url) == 'https://example.com/relative'
        assert normalize_url('relative', base_url) == 'https://example.com/relative'
        
        # Fragment should be removed
        assert normalize_url('https://example.com/page#fragment') == 'https://example.com/page'
        
        # Query should be preserved
        assert normalize_url('https://example.com/page?q=1') == 'https://example.com/page?q=1'
    
    def test_get_domain(self):
        """Test domain extraction."""
        assert get_domain('https://example.com/path') == 'example.com'
        assert get_domain('http://www.example.com') == 'www.example.com'
        assert get_domain('https://EXAMPLE.COM') == 'example.com'  # Lowercase
        assert get_domain('not-a-url') == ''
    
    def test_get_file_extension_from_url(self):
        """Test file extension extraction."""
        assert get_file_extension_from_url('https://example.com/image.jpg') == '.jpg'
        assert get_file_extension_from_url('https://example.com/video.MP4') == '.mp4'
        assert get_file_extension_from_url('https://example.com/file') == ''
        assert get_file_extension_from_url('https://example.com/path/file.pdf?query=1') == '.pdf'
    
    def test_is_external_link(self):
        """Test external link detection."""
        base_domain = 'example.com'
        
        assert is_external_link('https://example.com/path', base_domain) is False
        assert is_external_link('https://other.com/path', base_domain) is True
        assert is_external_link('https://sub.example.com/path', base_domain) is True
        assert is_external_link('https://EXAMPLE.COM/path', base_domain) is False  # Case insensitive


class TestFileUtils:
    """Test file utility functions."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        assert sanitize_filename('normal_file.txt') == 'normal_file.txt'
        assert sanitize_filename('file<with>bad:chars') == 'file_with_bad_chars'
        assert sanitize_filename('file/with\\path') == 'file_with_path'
        assert sanitize_filename('') == 'unnamed'
        assert sanitize_filename('   ...   ') == 'unnamed'
        
        # Test length limit
        long_name = 'a' * 300
        result = sanitize_filename(long_name)
        assert len(result) <= 255
    
    def test_get_content_type_from_extension(self):
        """Test content type detection."""
        assert get_content_type_from_extension('.jpg') == 'image'
        assert get_content_type_from_extension('.PNG') == 'image'
        assert get_content_type_from_extension('mp4') == 'video'
        assert get_content_type_from_extension('.AVI') == 'video'
        assert get_content_type_from_extension('.txt') == 'other'
        assert get_content_type_from_extension('') == 'other'
    
    def test_generate_unique_filename(self):
        """Test unique filename generation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # First file should use original name
            filename1 = generate_unique_filename(temp_path, 'test', '.txt')
            assert filename1 == 'test.txt'
            
            # Create the file
            (temp_path / filename1).touch()
            
            # Second file should get numbered suffix
            filename2 = generate_unique_filename(temp_path, 'test', '.txt')
            assert filename2 == 'test_1.txt'
            
            # Create second file
            (temp_path / filename2).touch()
            
            # Third file should get next number
            filename3 = generate_unique_filename(temp_path, 'test', '.txt')
            assert filename3 == 'test_2.txt'
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(0) == '0 B'
        assert format_file_size(1023) == '1023.0 B'
        assert format_file_size(1024) == '1.0 KB'
        assert format_file_size(1024 * 1024) == '1.0 MB'
        assert format_file_size(1024 * 1024 * 1024) == '1.0 GB'
        assert format_file_size(1536) == '1.5 KB'  # 1.5 KB
    
    def test_extract_filename_from_url(self):
        """Test filename extraction from URL."""
        assert extract_filename_from_url('https://example.com/file.txt') == 'file.txt'
        assert extract_filename_from_url('https://example.com/path/image.jpg') == 'image.jpg'
        assert extract_filename_from_url('https://example.com/') == 'example.com_page'
        assert extract_filename_from_url('https://example.com/path/') == 'example.com_page'
        
        # Test with query parameters
        result = extract_filename_from_url('https://example.com/file.pdf?download=1')
        assert result == 'file.pdf'


class TestTextUtils:
    """Test text utility functions."""
    
    def test_clean_text_content(self):
        """Test text content cleaning."""
        assert clean_text_content('') == ''
        assert clean_text_content('   ') == ''
        assert clean_text_content('normal text') == 'normal text'
        assert clean_text_content('  multiple   spaces  ') == 'multiple spaces'
        assert clean_text_content('line1\n\n\nline2') == 'line1 line2'
        assert clean_text_content('\t\ttab\t\tspaces\t') == 'tab spaces'
    
    def test_is_likely_content_url(self):
        """Test content URL detection."""
        # Should return True for likely content URLs
        assert is_likely_content_url('https://example.com/article') is True
        assert is_likely_content_url('https://example.com/blog/post') is True
        assert is_likely_content_url('https://example.com/image.jpg') is True
        
        # Should return False for non-content URLs
        assert is_likely_content_url('https://example.com/api/data') is False
        assert is_likely_content_url('https://example.com/ajax/load') is False
        assert is_likely_content_url('https://example.com/file.css') is False
        assert is_likely_content_url('https://example.com/script.js') is False
        assert is_likely_content_url('https://example.com/search?q=test') is False
        assert is_likely_content_url('https://example.com/login') is False


class TestFileOperations:
    """Test file operation utilities."""
    
    def test_create_directory(self):
        """Test directory creation."""
        from webscraper.utils import create_directory
        
        with tempfile.TemporaryDirectory() as temp_dir:
            test_path = Path(temp_dir) / 'new_dir' / 'nested'
            
            assert create_directory(test_path) is True
            assert test_path.exists()
            assert test_path.is_dir()
            
            # Should succeed even if directory exists
            assert create_directory(test_path) is True
    
    def test_get_file_hash(self):
        """Test file hash calculation."""
        from webscraper.utils import get_file_hash
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('test content')
            temp_file = f.name
        
        try:
            hash1 = get_file_hash(Path(temp_file))
            assert isinstance(hash1, str)
            assert len(hash1) == 32  # MD5 hash length
            
            # Same content should produce same hash
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
                f2.write('test content')
                temp_file2 = f2.name
            
            try:
                hash2 = get_file_hash(Path(temp_file2))
                assert hash1 == hash2
            finally:
                os.unlink(temp_file2)
        finally:
            os.unlink(temp_file)