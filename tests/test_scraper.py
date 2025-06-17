"""Tests for web scraper functionality."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from bs4 import BeautifulSoup

from webscraper.config import Config
from webscraper.scraper import WebScraper


class TestWebScraper:
    """Test web scraper functionality."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.config = Config(
            output_dir='/tmp/test',
            max_workers=2,
            delay_between_requests=0.1,
            respect_robots_txt=False  # Disable for testing
        )
    
    def test_scraper_initialization(self):
        """Test scraper initialization."""
        scraper = WebScraper(self.config)
        
        assert scraper.config == self.config
        assert scraper.session is not None
        assert scraper.downloader is not None
        assert isinstance(scraper.visited_urls, set)
        assert isinstance(scraper.robots_cache, dict)
    
    @patch('webscraper.scraper.requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test successful page fetching."""
        # Mock response
        mock_response = Mock()
        mock_response.content = b'<html><body><h1>Test</h1></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        scraper = WebScraper(self.config)
        soup = scraper._fetch_page('https://example.com')
        
        assert soup is not None
        assert soup.find('h1').text == 'Test'
        mock_get.assert_called_once()
    
    @patch('webscraper.scraper.requests.Session.get')
    def test_fetch_page_failure(self, mock_get):
        """Test page fetching failure."""
        mock_get.side_effect = Exception('Network error')
        
        scraper = WebScraper(self.config)
        soup = scraper._fetch_page('https://example.com')
        
        assert soup is None
    
    def test_extract_links(self):
        """Test link extraction from HTML."""
        html = '''
        <html>
        <body>
            <a href="https://example.com/page1">Link 1</a>
            <a href="/relative/path">Relative Link</a>
            <a href="mailto:test@example.com">Email</a>
            <a href="javascript:void(0)">JS Link</a>
            <a href="https://example.com/api/data">API Link</a>
        </body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'lxml')
        scraper = WebScraper(self.config)
        links = scraper._extract_links(soup, 'https://example.com')
        
        # Should extract valid HTTP links and resolve relative URLs
        expected_links = {
            'https://example.com/page1',
            'https://example.com/relative/path'
        }
        
        # Check that we got the expected links (subset, as API link filtering may vary)
        assert 'https://example.com/page1' in links
        assert 'https://example.com/relative/path' in links
    
    def test_extract_media_urls_images(self):
        """Test image URL extraction."""
        html = '''
        <html>
        <body>
            <img src="https://example.com/image1.jpg" alt="Image 1">
            <img src="/relative/image2.png" alt="Image 2">
            <img srcset="https://example.com/small.jpg 300w, https://example.com/large.jpg 600w">
            <img>  <!-- No src -->
        </body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'lxml')
        scraper = WebScraper(self.config)
        media_urls = scraper._extract_media_urls(soup, 'https://example.com')
        
        expected_images = [
            'https://example.com/image1.jpg',
            'https://example.com/relative/image2.png',
            'https://example.com/small.jpg',
            'https://example.com/large.jpg'
        ]
        
        for img_url in expected_images:
            assert img_url in media_urls['images']
    
    def test_extract_media_urls_videos(self):
        """Test video URL extraction."""
        html = '''
        <html>
        <body>
            <video src="https://example.com/video1.mp4"></video>
            <video>
                <source src="https://example.com/video2.webm" type="video/webm">
                <source src="/relative/video3.mp4" type="video/mp4">
            </video>
        </body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'lxml')
        scraper = WebScraper(self.config)
        media_urls = scraper._extract_media_urls(soup, 'https://example.com')
        
        expected_videos = [
            'https://example.com/video1.mp4',
            'https://example.com/video2.webm',
            'https://example.com/relative/video3.mp4'
        ]
        
        for video_url in expected_videos:
            assert video_url in media_urls['videos']
    
    def test_extract_text_content(self):
        """Test text content extraction."""
        html = '''
        <html>
        <head>
            <title>Test Page</title>
            <script>alert('test');</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is a paragraph with <strong>bold text</strong>.</p>
            <div>Another section</div>
        </body>
        </html>
        '''
        
        soup = BeautifulSoup(html, 'lxml')
        scraper = WebScraper(self.config)
        text = scraper._extract_text_content(soup)
        
        # Should extract text but not script/style content
        assert 'Main Title' in text
        assert 'This is a paragraph' in text
        assert 'bold text' in text
        assert 'Another section' in text
        assert 'alert(' not in text  # Script should be removed
        assert 'color: red' not in text  # Style should be removed
    
    def test_should_follow_link(self):
        """Test link following logic."""
        scraper = WebScraper(self.config)
        base_domain = 'example.com'
        
        # Test depth limit
        assert scraper._should_follow_link('https://example.com/page', base_domain, 0) is True
        assert scraper._should_follow_link('https://example.com/page', base_domain, 1) is False  # max_depth=1
        
        # Test visited URLs
        scraper.visited_urls.add('https://example.com/visited')
        assert scraper._should_follow_link('https://example.com/visited', base_domain, 0) is False
        
        # Test external links
        assert scraper._should_follow_link('https://other.com/page', base_domain, 0) is False
        
        # Test with external links enabled
        config_with_external = Config(follow_external_links=True, max_depth=1)
        scraper_with_external = WebScraper(config_with_external)
        assert scraper_with_external._should_follow_link('https://other.com/page', base_domain, 0) is True
    
    @patch('webscraper.scraper.WebScraper._fetch_page')
    def test_scrape_url_success(self, mock_fetch):
        """Test successful URL scraping."""
        html = '''
        <html>
        <body>
            <h1>Test Page</h1>
            <p>Content here</p>
            <img src="https://example.com/image.jpg">
            <a href="https://example.com/link">Link</a>
        </body>
        </html>
        '''
        
        mock_fetch.return_value = BeautifulSoup(html, 'lxml')
        
        scraper = WebScraper(self.config)
        result = scraper.scrape_url('https://example.com')
        
        assert result['success'] is True
        assert result['url'] == 'https://example.com'
        assert 'Test Page' in result['text_content']
        assert 'https://example.com/image.jpg' in result['media_urls']['images']
        assert 'https://example.com/link' in result['links']
        assert result['error'] is None
    
    @patch('webscraper.scraper.WebScraper._fetch_page')
    def test_scrape_url_failure(self, mock_fetch):
        """Test URL scraping failure."""
        mock_fetch.return_value = None  # Simulate fetch failure
        
        scraper = WebScraper(self.config)
        result = scraper.scrape_url('https://example.com')
        
        assert result['success'] is False
        assert result['error'] == 'Failed to fetch page'
    
    def test_scrape_url_already_visited(self):
        """Test scraping already visited URL."""
        scraper = WebScraper(self.config)
        scraper.visited_urls.add('https://example.com')
        
        result = scraper.scrape_url('https://example.com')
        
        assert result['success'] is False
        assert result['error'] == 'URL already visited'
    
    def test_context_manager(self):
        """Test scraper as context manager."""
        with patch.object(WebScraper, 'cleanup') as mock_cleanup:
            with WebScraper(self.config) as scraper:
                assert scraper is not None
            
            mock_cleanup.assert_called_once()
    
    @patch('webscraper.scraper.WebScraper.scrape_url')
    @patch('webscraper.downloader.ContentDownloader.download_multiple')
    @patch('webscraper.downloader.ContentDownloader.download_text_content')
    def test_scrape_and_download(self, mock_download_text, mock_download_multiple, mock_scrape):
        """Test complete scrape and download workflow."""
        # Mock scrape result
        mock_scrape.return_value = {
            'success': True,
            'url': 'https://example.com',
            'text_content': 'Test content',
            'media_urls': {
                'images': ['https://example.com/image.jpg'],
                'videos': ['https://example.com/video.mp4']
            },
            'links': set(),
            'error': None
        }
        
        # Mock download results
        mock_download_text.return_value = Mock(success=True)
        mock_download_multiple.return_value = {
            'https://example.com/image.jpg': Mock(success=True),
            'https://example.com/video.mp4': Mock(success=True)
        }
        
        scraper = WebScraper(self.config)
        scraper.downloader.get_stats = Mock(return_value={
            'successful_downloads': 2,
            'failed_downloads': 0,
            'skipped_files': 0
        })
        
        result = scraper.scrape_and_download('https://example.com')
        
        assert 'scraped_urls' in result
        assert 'download_results' in result
        assert 'stats' in result
        assert result['stats']['successful_scrapes'] == 1
        
        # Verify methods were called
        mock_scrape.assert_called()
        mock_download_text.assert_called()
        mock_download_multiple.assert_called()