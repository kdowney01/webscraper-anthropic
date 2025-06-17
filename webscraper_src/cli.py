"""Command line interface for the web scraper."""

import sys
import logging
from pathlib import Path
from typing import List, Optional
import click
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress
from rich.table import Table

from .config import Config
from .scraper import WebScraper
from .utils import is_valid_url, format_file_size

console = Console()


def setup_logging(log_level: str, log_file: Optional[str] = None) -> None:
    """Setup logging configuration."""
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatters
    console_formatter = logging.Formatter('%(message)s')
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Add rich console handler
    console_handler = RichHandler(console=console, show_time=False, show_path=False)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def validate_urls(urls: List[str]) -> List[str]:
    """Validate and filter URLs."""
    valid_urls = []
    for url in urls:
        if is_valid_url(url):
            valid_urls.append(url)
        else:
            console.print(f"[red]Invalid URL: {url}[/red]")
    
    return valid_urls


def display_results_summary(results: dict) -> None:
    """Display scraping results summary."""
    if 'combined_stats' in results:
        # Multiple URLs
        stats = results['combined_stats']
        table = Table(title="Scraping Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total URLs", str(stats['total_urls']))
        table.add_row("Successful Scrapes", str(stats['successful_scrapes']))
        table.add_row("Failed Scrapes", str(stats['failed_scrapes']))
        table.add_row("Media Files Found", str(stats['total_media_found']))
        table.add_row("Files Downloaded", str(stats['total_downloads']))
        
    else:
        # Single URL
        stats = results['stats']
        download_stats = stats.get('download_stats', {})
        
        table = Table(title="Scraping Summary")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("URLs Scraped", str(stats['total_urls_scraped']))
        table.add_row("Successful Scrapes", str(stats['successful_scrapes']))
        table.add_row("Failed Scrapes", str(stats['failed_scrapes']))
        table.add_row("Media Files Found", str(stats['total_media_found']))
        table.add_row("Files Downloaded", str(download_stats.get('successful_downloads', 0)))
        table.add_row("Download Failures", str(download_stats.get('failed_downloads', 0)))
        table.add_row("Files Skipped", str(download_stats.get('skipped_files', 0)))
        
        if download_stats.get('total_bytes', 0) > 0:
            table.add_row("Total Size", format_file_size(download_stats['total_bytes']))
    
    console.print(table)


@click.command()
@click.argument('urls', nargs=-1, required=True)
@click.option('--config', '-c', 'config_file', 
              help='Configuration file path', type=click.Path(exists=True))
@click.option('--output', '-o', 'output_dir',
              help='Output directory for downloaded content', type=click.Path())
@click.option('--max-depth', '-d', default=None, type=int,
              help='Maximum crawling depth (overrides config)')
@click.option('--max-workers', '-w', default=None, type=int,
              help='Maximum number of concurrent downloads (overrides config)')
@click.option('--delay', default=None, type=float,
              help='Delay between requests in seconds (overrides config)')
@click.option('--user-agent', default=None,
              help='User agent string (overrides config)')
@click.option('--no-images', is_flag=True,
              help='Skip image downloads')
@click.option('--no-videos', is_flag=True,
              help='Skip video downloads')
@click.option('--no-text', is_flag=True,
              help='Skip text content extraction')
@click.option('--ignore-robots', is_flag=True,
              help='Ignore robots.txt restrictions')
@click.option('--log-level', default=None,
              type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR'], case_sensitive=False),
              help='Logging level (overrides config)')
@click.option('--log-file', default=None,
              help='Log file path (overrides config)')
@click.option('--dry-run', is_flag=True,
              help='Show what would be scraped without downloading')
@click.version_option(version='0.1.0', prog_name='webscraper')
def main(urls: tuple, config_file: Optional[str], output_dir: Optional[str],
         max_depth: Optional[int], max_workers: Optional[int], delay: Optional[float],
         user_agent: Optional[str], no_images: bool, no_videos: bool, no_text: bool,
         ignore_robots: bool, log_level: Optional[str], log_file: Optional[str],
         dry_run: bool) -> None:
    """
    Web Scraper - Download content from websites.
    
    Scrapes text, images, and videos from the specified URLs and saves them
    to organized local directories.
    
    Examples:
        webscraper https://example.com
        webscraper --config config.yaml https://example.com
        webscraper -d 2 -w 10 https://example.com https://another.com
    """
    try:
        # Load configuration
        if config_file:
            try:
                config = Config.from_file(config_file)
                console.print(f"[green]Loaded configuration from: {config_file}[/green]")
            except Exception as e:
                console.print(f"[red]Error loading config file: {e}[/red]")
                sys.exit(1)
        else:
            config = Config()
        
        # Override config with CLI arguments
        if max_depth is not None:
            config.max_depth = max_depth
        if max_workers is not None:
            config.max_workers = max_workers
        if delay is not None:
            config.delay_between_requests = delay
        if user_agent is not None:
            config.user_agent = user_agent
        if no_images:
            config.download_images = False
        if no_videos:
            config.download_videos = False
        if no_text:
            config.download_text = False
        if ignore_robots:
            config.respect_robots_txt = False
        if log_level is not None:
            config.log_level = log_level
        if log_file is not None:
            config.log_file = log_file
        if output_dir is not None:
            config.output_dir = output_dir
        
        # Validate configuration
        try:
            config.validate()
        except ValueError as e:
            console.print(f"[red]Configuration error: {e}[/red]")
            sys.exit(1)
        
        # Setup logging
        setup_logging(config.log_level, config.log_file)
        
        # Validate URLs
        url_list = list(urls)
        valid_urls = validate_urls(url_list)
        
        if not valid_urls:
            console.print("[red]No valid URLs provided[/red]")
            sys.exit(1)
        
        if len(valid_urls) < len(url_list):
            console.print(f"[yellow]Proceeding with {len(valid_urls)} valid URLs[/yellow]")
        
        # Display configuration summary
        console.print(f"[blue]Configuration:[/blue]")
        console.print(f"  Output directory: {config.output_dir}")
        console.print(f"  Max depth: {config.max_depth}")
        console.print(f"  Max workers: {config.max_workers}")
        console.print(f"  Delay between requests: {config.delay_between_requests}s")
        console.print(f"  Download images: {config.download_images}")
        console.print(f"  Download videos: {config.download_videos}")
        console.print(f"  Download text: {config.download_text}")
        console.print(f"  Respect robots.txt: {config.respect_robots_txt}")
        console.print()
        
        if dry_run:
            console.print("[yellow]DRY RUN - No files will be downloaded[/yellow]")
            console.print(f"Would scrape {len(valid_urls)} URLs:")
            for url in valid_urls:
                console.print(f"  - {url}")
            return
        
        # Create scraper and start scraping
        with WebScraper(config) as scraper:
            console.print(f"[green]Starting scrape of {len(valid_urls)} URLs...[/green]")
            
            if len(valid_urls) == 1:
                # Single URL
                results = scraper.scrape_and_download(valid_urls[0])
            else:
                # Multiple URLs
                results = scraper.scrape_multiple_urls(valid_urls)
            
            # Display results
            console.print()
            display_results_summary(results)
            
            # Show output directory
            if Path(config.output_dir).exists():
                console.print(f"[green]Content saved to: {config.output_dir}[/green]")
            
            console.print("[green]Scraping completed![/green]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Scraping interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        logging.exception("Unexpected error occurred")
        sys.exit(1)


@click.command()
@click.argument('config_file', required=False)
def init_config(config_file: Optional[str] = None) -> None:
    """Initialize a new configuration file."""
    if config_file is None:
        config_file = "config.yaml"
    
    if Path(config_file).exists():
        if not click.confirm(f"Configuration file {config_file} already exists. Overwrite?"):
            console.print("[yellow]Configuration creation cancelled[/yellow]")
            return
    
    try:
        config = Config()
        config.save_to_file(config_file)
        console.print(f"[green]Configuration file created: {config_file}[/green]")
        console.print("Edit this file to customize your scraping settings.")
    except Exception as e:
        console.print(f"[red]Error creating configuration file: {e}[/red]")
        sys.exit(1)


# Create CLI group
@click.group()
def cli():
    """Web Scraper - Download content from websites."""
    pass


# Add commands to group
cli.add_command(main, name='scrape')
cli.add_command(init_config, name='init')


if __name__ == '__main__':
    main()