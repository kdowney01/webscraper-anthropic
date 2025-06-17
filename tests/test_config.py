"""Tests for configuration management."""

import os
import tempfile
import pytest
import yaml
from pathlib import Path

from webscraper.config import Config


class TestConfig:
    """Test configuration functionality."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.output_dir == "./downloads"
        assert config.user_agent == "WebScraper/1.0"
        assert config.max_workers == 5
        assert config.delay_between_requests == 1.0
        assert config.download_images is True
        assert config.download_videos is True
        assert config.download_text is True
        assert config.max_depth == 1
        assert config.respect_robots_txt is True
    
    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_data = {
            'output_dir': '/tmp/test',
            'max_workers': 10,
            'download_images': False,
            'user_agent': 'TestAgent/1.0'
        }
        
        config = Config.from_dict(config_data)
        
        assert config.output_dir == '/tmp/test'
        assert config.max_workers == 10
        assert config.download_images is False
        assert config.user_agent == 'TestAgent/1.0'
        # Other values should remain default
        assert config.download_videos is True
        assert config.max_depth == 1
    
    def test_config_from_file(self):
        """Test loading config from YAML file."""
        config_data = {
            'output_dir': '/tmp/yaml_test',
            'max_workers': 8,
            'delay_between_requests': 2.5,
            'image_extensions': ['jpg', 'png'],
            'respect_robots_txt': False
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_file = f.name
        
        try:
            config = Config.from_file(temp_file)
            
            assert config.output_dir == '/tmp/yaml_test'
            assert config.max_workers == 8
            assert config.delay_between_requests == 2.5
            assert config.image_extensions == ['jpg', 'png']
            assert config.respect_robots_txt is False
        finally:
            os.unlink(temp_file)
    
    def test_config_from_nonexistent_file(self):
        """Test loading config from nonexistent file."""
        with pytest.raises(FileNotFoundError):
            Config.from_file('/nonexistent/config.yaml')
    
    def test_config_validation_valid(self):
        """Test valid configuration passes validation."""
        config = Config()
        # Should not raise exception
        config.validate()
    
    def test_config_validation_invalid_workers(self):
        """Test validation fails for invalid max_workers."""
        config = Config(max_workers=0)
        
        with pytest.raises(ValueError, match="max_workers must be at least 1"):
            config.validate()
    
    def test_config_validation_negative_delay(self):
        """Test validation fails for negative delay."""
        config = Config(delay_between_requests=-1.0)
        
        with pytest.raises(ValueError, match="delay_between_requests cannot be negative"):
            config.validate()
    
    def test_config_validation_invalid_log_level(self):
        """Test validation fails for invalid log level."""
        config = Config(log_level="INVALID")
        
        with pytest.raises(ValueError, match="log_level must be one of"):
            config.validate()
    
    def test_to_dict(self):
        """Test converting config to dictionary."""
        config = Config(output_dir='/test', max_workers=3)
        config_dict = config.to_dict()
        
        assert isinstance(config_dict, dict)
        assert config_dict['output_dir'] == '/test'
        assert config_dict['max_workers'] == 3
        assert 'user_agent' in config_dict
    
    def test_save_to_file(self):
        """Test saving config to file."""
        config = Config(output_dir='/test/save', max_workers=7)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            config.save_to_file(temp_file)
            
            # Load and verify
            loaded_config = Config.from_file(temp_file)
            assert loaded_config.output_dir == '/test/save'
            assert loaded_config.max_workers == 7
        finally:
            os.unlink(temp_file)
    
    def test_get_output_path_no_domain(self):
        """Test getting output path without domain organization."""
        config = Config(output_dir='/base', organize_by_domain=False)
        path = config.get_output_path()
        
        assert path == Path('/base')
    
    def test_get_output_path_with_domain(self):
        """Test getting output path with domain organization."""
        config = Config(output_dir='/base', organize_by_domain=True)
        path = config.get_output_path('example.com')
        
        assert path == Path('/base/example.com')
    
    def test_get_content_path_no_subdirs(self):
        """Test getting content path without type subdirectories."""
        config = Config(create_subdirs_for_types=False)
        base_path = Path('/test')
        
        path = config.get_content_path(base_path, 'image')
        assert path == base_path
    
    def test_get_content_path_with_subdirs(self):
        """Test getting content path with type subdirectories."""
        config = Config(create_subdirs_for_types=True)
        base_path = Path('/test')
        
        image_path = config.get_content_path(base_path, 'image')
        video_path = config.get_content_path(base_path, 'video')
        text_path = config.get_content_path(base_path, 'text')
        
        assert image_path == Path('/test/images')
        assert video_path == Path('/test/videos')
        assert text_path == Path('/test/text')
    
    def test_is_supported_image(self):
        """Test image format detection."""
        config = Config()
        
        assert config.is_supported_image('.jpg') is True
        assert config.is_supported_image('png') is True
        assert config.is_supported_image('.PNG') is True
        assert config.is_supported_image('.txt') is False
        assert config.is_supported_image('mp4') is False
    
    def test_is_supported_video(self):
        """Test video format detection."""
        config = Config()
        
        assert config.is_supported_video('.mp4') is True
        assert config.is_supported_video('webm') is True
        assert config.is_supported_video('.AVI') is True
        assert config.is_supported_video('.jpg') is False
        assert config.is_supported_video('txt') is False
    
    def test_should_download_content_type(self):
        """Test content type download settings."""
        config = Config(download_images=True, download_videos=False, download_text=True)
        
        assert config.should_download_content_type('image') is True
        assert config.should_download_content_type('video') is False
        assert config.should_download_content_type('text') is True
        assert config.should_download_content_type('other') is False
    
    def test_get_size_limit(self):
        """Test size limit calculation."""
        config = Config(
            max_file_size=10,  # 10 MB
            max_image_size=5,  # 5 MB
            max_video_size=50  # 50 MB
        )
        
        # Size limits should be in bytes
        assert config.get_size_limit('image') == 5 * 1024 * 1024
        assert config.get_size_limit('video') == 50 * 1024 * 1024
        assert config.get_size_limit('other') == 10 * 1024 * 1024
        
        # Test with no limits
        config_no_limit = Config(max_file_size=0, max_image_size=0, max_video_size=0)
        assert config_no_limit.get_size_limit('image') == 0
        assert config_no_limit.get_size_limit('video') == 0