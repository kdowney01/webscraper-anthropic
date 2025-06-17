# Web Scraper

A Python application for scraping web content including text, images, and videos from websites and organizing them in local directory structures.

## Features

- Download text content, images, and videos from web pages
- Respect robots.txt and implement ethical scraping practices
- Configurable rate limiting and concurrent downloads
- Organized directory structure with duplicate detection
- Progress tracking and comprehensive logging
- Cross-platform compatibility

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd web-scraper
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Usage

### Command Line Interface

Basic usage:
```bash
python3 -m webscraper_src.cli https://example.com
```

With configuration file:
```bash
python3 -m webscraper_src.cli --config config.yaml https://example.com
```

Multiple URLs:
```bash
python3 -m webscraper_src.cli https://example1.com https://example2.com
```

### Configuration

Copy the example configuration file:
```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml` to customize settings like output directory, file types, and crawling behavior.

## Development

### Running Tests

```bash
pytest
```

With coverage:
```bash
pytest --cov=webscraper
```

### Code Formatting

```bash
black webscraper tests
```

### Type Checking

```bash
mypy webscraper
```

### Linting

```bash
flake8 webscraper
```

## Project Structure

```
webscraper/
├── webscraper/          # Main package
│   ├── __init__.py
│   ├── cli.py          # Command line interface
│   ├── scraper.py      # Core scraping logic
│   ├── downloader.py   # Content download handling
│   ├── config.py       # Configuration management
│   └── utils.py        # Utility functions
├── tests/              # Test files
├── docs/               # Documentation
├── examples/           # Example scripts
└── requirements.txt    # Dependencies
```

## License

MIT License - see LICENSE file for details.