import os
import requests
from pathlib import Path
from rich import print
from loguru import logger
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from utils import dumped_html_path


class HTMLScraper:
    BASE_URL_TO_SCRAPE = 'https://docs.djangoproject.com'
    DOCS_LANG = 'en'
    DJANGO_VERSION_TO_SCRAPE = '6.0'
    LANG_TO_SCRAPE = 'en'
    DJANGO_DOCS_ROOT_URL = f'{BASE_URL_TO_SCRAPE}/{LANG_TO_SCRAPE}/{DJANGO_VERSION_TO_SCRAPE}'

    def __init__(self, base_url=None   ):
        self.already_scraped_urls = set()
        self.already_scraped_files = self.find_already_scraped_files()
        logger.info(f'Found {len(self.already_scraped_files)} scraped files on disk already.')
        if base_url:
            self.urls_to_scrape = set([base_url])
        else:
            self.urls_to_scrape = set([self.DJANGO_DOCS_ROOT_URL])
        self.page_not_found_filename = '404_urls.txt'

    def dumped_html_path(self):
        return dumped_html_path()

    def find_already_scraped_files(self):
        res = set()
        path = self.dumped_html_path()
        # ensure directory exists
        path.mkdir(parents=True, exist_ok=True)
        for file in os.listdir(path):
            if file.endswith(".html"):
                res.add(path / Path(file))
        return res

    def url_to_filepath(self, url: str) -> Path:
        filename = url.replace('//', '_').replace('/', '_').replace('.', '_').replace(':', '_')
        path = self.dumped_html_path() / Path(filename + '.html')
        return path
    
    def get_404_urls(self) -> set[str]:
        try:
            with open(self.page_not_found_filename, 'r') as f:
                return set(f.read().split(';'))
        except FileNotFoundError:
            return set()
            
    def add_to_404_urls(self, url: str):
        not_found_urls = self.get_404_urls()
        not_found_urls.add(url)
        with open(self.page_not_found_filename, 'w') as f:
                f.write(';'.join(not_found_urls))



    def get_html(self, url) -> tuple[str, bool]:
        filepath = self.url_to_filepath(url)
        if filepath in self.already_scraped_files:
            logger.info(f'URL HTML file already on disk, skipping: {filepath=}')
            with open(filepath, 'r') as f:
                return f.read(), False

        logger.info(f'Fetching URL: {url=}')
        resp = requests.get(url, timeout=10)

        if resp.status_code == 404:
            self.add_to_404_urls(url)

        resp.raise_for_status()

        self.already_scraped_urls.add(url)

        logger.info(f'Scraped: {url=}')

        not_found_page_msg = "Looks like you followed a bad link. If you think it's our fault, please"
        if not_found_page_msg in resp.text:
            raise ValueError(f"Page not found: {url=}")

        with open(filepath, 'w') as f:
            f.write(resp.text)

        logger.info(f'Dumped HTML to file: {filepath}')

        self.already_scraped_files.add(filepath)

        return resp.text, True
    
    def assert_en_lang_in_url(self, url: str):
        parts = url.split(self.BASE_URL_TO_SCRAPE + '/')
        if len(parts) < 2:
            raise self.LanguageNotMatchedException(f'could not parse language -> {url=}')
        page_language = parts[1].split('/')[0]
        if page_language != self.LANG_TO_SCRAPE:
            raise self.LanguageNotMatchedException(f'{page_language=} -> {url=}')
        
    def assert_version_in_url(self, url: str):
        parts = url.split(self.BASE_URL_TO_SCRAPE + '/' + self.LANG_TO_SCRAPE + '/')
        if len(parts) < 2:
            raise self.VersionNotMatchedException(f'could not parse version -> {url=}')
        page_version = parts[1].split('/')[0]
        if not page_version.startswith(self.DJANGO_VERSION_TO_SCRAPE):
            raise self.VersionNotMatchedException(f'{page_version=} -> {url=}')
        
    def assert_url_is_not_excluded(self, url):
        if not url.startswith(self.BASE_URL_TO_SCRAPE):
                raise self.ExcludedURLException(f'{url=} , {url=}')
        
    def assert_url_is_not_404(self, url: str):
        if url in self.get_404_urls():
            raise self.PageNotFoundException(f"Previously marked as 404: {url}")

    def get_soup(self, resp: str):
        return BeautifulSoup(resp, 'html.parser')
    
    def assert_url_is_valid(self, url: str):
        self.assert_url_is_not_excluded(url)
        self.assert_en_lang_in_url(url)
        self.assert_version_in_url(url)
        self.assert_url_is_not_404(url)
    
    def make_full_valid_url(self, link, page_url:str) -> str:
        def remove_hashtag(text: str) -> str:
            return text.split('#')[0]
        
        url = link.get('href')

        if not url:
            raise self.BlankUrlException(url)
        
        elif url.startswith('http://'):
            raise self.NonHTTPSPageException(url)
        
        elif url.startswith('https://'):
            self.assert_url_is_valid(url)
            return remove_hashtag(url)
        
        elif url.startswith('#'):
            raise self.LinkToCurrentPageException(url)
        
        elif link.has_attr('class'):
            if 'reference' in link['class'] and 'internal' in link['class']:
                full_url = f"{self.DJANGO_DOCS_ROOT_URL}/{url.lstrip('/')}"
                self.assert_url_is_valid(full_url)
                return remove_hashtag(full_url)
        
        elif url.strip('/') in {'contents', 'intro'}:
            full_url = f"{self.DJANGO_DOCS_ROOT_URL}/{url.lstrip('/')}"
            self.assert_url_is_valid(full_url)
            return remove_hashtag(full_url)
        
        elif url.startswith('/en/stable/'):
            full_url = f"{self.DJANGO_DOCS_ROOT_URL}/{url.split('/en/stable/')[-1]}"
            self.assert_url_is_valid(full_url)
            return remove_hashtag(full_url)
        
        elif url.startswith('..'):
            full_url = urljoin(page_url, url)
            self.assert_url_is_valid(full_url)
            return remove_hashtag(full_url)
        
        try:
            rel = link['rel'][0]
            if rel == 'next':
                full_url = urljoin(page_url, url)
                self.assert_url_is_valid(full_url)
                return remove_hashtag(full_url)
        except KeyError:
            pass

        raise ValueError(f'Could not make full valid URL from link: {url=} {link=}')

    def extract_links(self, soup):
        urls = soup.find_all('a')
        return urls
    
    def extend_urls_to_scrape(self, links, page_url: str):
        for link in links:
            try:
                url = self.make_full_valid_url(link, page_url)
            except self.Error as e:
                # logger.exception(e)
                continue

            if not url:
                continue

            if url in self.get_404_urls():
                continue

            if url in self.already_scraped_urls:
                logger.info(f'Will not scrape {url} again!')
                continue

            self.urls_to_scrape.add(url)
    
    def scrape_all(self):
        not_found_pages = set()
        while self.urls_to_scrape:
            logger.info(f'Remaining URLs to scrape: {len(self.urls_to_scrape)=}')
            url = self.urls_to_scrape.pop()
            try:
                resp, scraped = self.get_html(url)
            except self.Error as e:
                # logger.exception(e)
                continue
            except self.PageNotFoundException:
                not_found_pages.add(url)
                continue

            logger.info(f'Got HTML for URL: {url=}')

            soup = self.get_soup(resp)
            links = self.extract_links(soup)
            self.extend_urls_to_scrape(links, url)

            if scraped:
                x = 1
                logger.info(f'Going to sleep {x} seconds...')
                logger.info(f'Remaining URLs to scrape: {len(self.urls_to_scrape)=}')
                sleep(x)
        
        print(not_found_pages)

    class Error(Exception):
        pass

    class ExcludedURLException(Error):
        pass

    class LanguageNotMatchedException(Error):
        pass

    class VersionNotMatchedException(Error):
        pass

    class LinkToCurrentPageException(Error):
        pass

    class NonHTTPSPageException(Error):
        pass

    class BlankUrlException(Error):
        pass

    class PageNotFoundException(Exception):
        pass