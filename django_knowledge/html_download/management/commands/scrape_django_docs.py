import djclick as click
from html_download.html_scraper import HTMLScraper
from html_download.models import NotFoundURL, URLToVisit

@click.command()
@click.argument('base_url', default='https://docs.djangoproject.com/en/6.0/')
@click.option('--delete-existing', is_flag=True, default=False)
def command(base_url, delete_existing=False):
    if delete_existing:
        NotFoundURL.objects.all().delete()
        URLToVisit.objects.all().delete()
        click.echo('Deleted existing NotFoundURL and URLToVisit entries.')

    breakpoint()

    scraper = HTMLScraper(base_url=base_url)
    scraper.scrape_all()