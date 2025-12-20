from pathlib import Path

def dumped_html_path():
        return Path('.') / Path('scraped_data') / Path('official_django_docs') / Path('full_page')