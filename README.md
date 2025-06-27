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
git clone https://github.com/kdowney01/webscraper-anthropic.git
cd webscraper-anthropic
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# Core scraping dependencies
python3 -m pip install --user requests beautifulsoup4 lxml click rich pyyaml tqdm validators colorlog filetype

# Web interface dependencies
python3 -m pip install --user flask flask-socketio
```

4. For development:
```bash
python3 -m pip install --user pytest pytest-cov black flake8 mypy
```

## Usage

### Web Interface (Recommended)

Launch the modern web interface:
```bash
python3 run_web_interface.py
```

Then open your browser to: **http://localhost:8080**

The web interface provides:
- 🎯 **Interactive form** with real-time validation
- 📊 **Live progress tracking** with WebSocket updates
- 📁 **Job history** with re-run functionality
- 📦 **ZIP downloads** of scraped content
- 📱 **Responsive design** for mobile and desktop

### Command Line Interface

Basic usage:
```bash
./webscraper https://example.com
```

With configuration file:
```bash
./webscraper --config config.yaml https://example.com
```

Multiple URLs:
```bash
./webscraper https://example1.com https://example2.com
```

Alternative (using Python module directly):
```bash
python3 -m webscraper_src.cli https://example.com
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