"""Configuration management for the web scraper."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Config:
    """Configuration class for web scraper settings."""
    
    # General settings
    output_dir: str = "/Users/kyledowney/projects/webscraper/scraped"
    user_agent: str = "WebScraper/1.0"
    max_workers: int = 5
    delay_between_requests: float = 1.0
    
    # File type filters
    download_images: bool = True
    download_videos: bool = True
    download_text: bool = True
    
    # Supported extensions
    image_extensions: List[str] = field(default_factory=lambda: [
        "jpg", "jpeg", "png", "gif", "webp", "svg"
    ])
    video_extensions: List[str] = field(default_factory=lambda: [
        "mp4", "webm", "avi", "mov", "mkv"
    ])
    
    # Size limits (in MB, 0 = no limit)
    max_file_size: int = 100
    max_image_size: int = 50
    max_video_size: int = 500
    
    # Crawling settings
    max_depth: int = 1
    follow_external_links: bool = False
    respect_robots_txt: bool = True
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 2.0
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "webscraper.log"
    
    # Directory structure
    organize_by_domain: bool = True
    organize_by_date: bool = False
    create_subdirs_for_types: bool = True
    
    @classmethod
    def from_file(cls, config_path: str) -> "Config":
        """Load configuration from a YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        return cls.from_dict(config_data or {})
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create configuration from dictionary."""
        # Filter out keys that don't match class fields
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_keys}
        
        return cls(**filtered_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to a YAML file."""
        config_dict = self.to_dict()
        
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)
    
    def validate(self) -> None:
        """Validate configuration values."""
        errors = []
        
        if self.max_workers < 1:
            errors.append("max_workers must be at least 1")
        
        if self.delay_between_requests < 0:
            errors.append("delay_between_requests cannot be negative")
        
        if self.max_depth < 0:
            errors.append("max_depth cannot be negative")
        
        if self.max_retries < 0:
            errors.append("max_retries cannot be negative")
        
        if self.retry_delay < 0:
            errors.append("retry_delay cannot be negative")
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"log_level must be one of: {', '.join(valid_log_levels)}")
        
        # Ensure output directory parent exists
        output_path = Path(self.output_dir)
        if not output_path.parent.exists():
            errors.append(f"Parent directory of output_dir does not exist: {output_path.parent}")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")
    
    def get_output_path(self, domain: Optional[str] = None) -> Path:
        """Get the output path for downloaded content."""
        base_path = Path(self.output_dir)
        
        if self.organize_by_domain and domain:
            base_path = base_path / domain
        
        if self.organize_by_date:
            from datetime import datetime
            date_str = datetime.now().strftime("%Y-%m-%d")
            base_path = base_path / date_str
        
        return base_path
    
    def get_content_path(self, base_path: Path, content_type: str) -> Path:
        """Get the path for specific content type."""
        if not self.create_subdirs_for_types:
            return base_path
        
        if content_type == "image":
            return base_path / "images"
        elif content_type == "video":
            return base_path / "videos"
        elif content_type == "text":
            return base_path / "text"
        else:
            return base_path / "other"
    
    def is_supported_image(self, extension: str) -> bool:
        """Check if file extension is a supported image format."""
        return extension.lower().lstrip('.') in [ext.lower() for ext in self.image_extensions]
    
    def is_supported_video(self, extension: str) -> bool:
        """Check if file extension is a supported video format."""
        return extension.lower().lstrip('.') in [ext.lower() for ext in self.video_extensions]
    
    def should_download_content_type(self, content_type: str) -> bool:
        """Check if content type should be downloaded based on settings."""
        if content_type == "image":
            return self.download_images
        elif content_type == "video":
            return self.download_videos
        elif content_type == "text":
            return self.download_text
        return False
    
    def get_size_limit(self, content_type: str) -> int:
        """Get size limit for content type in bytes (0 = no limit)."""
        if content_type == "image" and self.max_image_size > 0:
            return self.max_image_size * 1024 * 1024
        elif content_type == "video" and self.max_video_size > 0:
            return self.max_video_size * 1024 * 1024
        elif self.max_file_size > 0:
            return self.max_file_size * 1024 * 1024
        return 0