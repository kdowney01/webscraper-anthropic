# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Web Scraper - A Python application for scraping web content including text, images, and videos from websites. The application organizes downloaded content in structured local directories and implements ethical scraping practices.

**Technology Stack:**
- Python 3.8+
- requests + BeautifulSoup for web scraping
- click for CLI interface
- rich for progress display
- YAML for configuration
- pytest for testing

## Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .         # Install in development mode
pip install -e ".[dev]"  # Install with dev dependencies

# Testing
pytest                   # Run all tests
pytest --cov=webscraper  # Run tests with coverage
pytest -v               # Verbose output

# Code Quality
black webscraper tests   # Format code
flake8 webscraper       # Lint code
mypy webscraper         # Type checking

# Running the application
./webscraper --help                              # Show help
./webscraper https://example.com                 # Basic scraping
./webscraper --config config.yaml https://example.com  # With config

# Alternative (using Python module directly)
python3 -m webscraper_src.cli --help                              # Show help
python3 -m webscraper_src.cli https://example.com                 # Basic scraping
python3 -m webscraper_src.cli --config config.yaml https://example.com  # With config
```

## Architecture Notes

**Core Components:**
- `webscraper/cli.py` - Command line interface using click
- `webscraper/scraper.py` - Main scraping logic with BeautifulSoup
- `webscraper/downloader.py` - Content download handling with progress tracking
- `webscraper/config.py` - Configuration management (YAML/dict)
- `webscraper/utils.py` - Utility functions for URL handling, file operations

**Key Design Patterns:**
- Configuration-driven behavior (YAML config file)
- Concurrent downloads using ThreadPoolExecutor
- Progress tracking with rich/tqdm
- Ethical scraping (robots.txt compliance, rate limiting)
- Structured output directories organized by domain/content type

**Testing Strategy:**
- Unit tests for each module in `tests/`
- Mock external HTTP requests in tests
- Test configuration loading and validation
- Test file organization and duplicate handling