import djclick as click
from html_download.html_scraper import HTMLScraper

@click.command()
@click.argument('base_url', default='https://docs.djangoproject.com/en/6.0/')
def command(base_url):
    scraper = HTMLScraper(base_url=base_url)
    scraper.scrape_all()