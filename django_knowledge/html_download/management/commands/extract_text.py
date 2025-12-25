import djclick as click
from loguru import logger

from text_extraction.to_markdown import convert_to_makdown
from html_download.models import Page


@click.command()
def command():
    for page in Page.objects.all():
        md = convert_to_makdown(page.html_content)
        page.add_extracted_text(md)
        logger.info(f"Extracted text for {page.url}")
