import glob, os
import requests
from pathlib import Path
from rich import print
from loguru import logger
from time import sleep
from bs4 import BeautifulSoup

from utils import dumped_html_path


class HTMLScraper:
    BASE_URL_TO_SCRAPE = 'https://docs.djangoproject.com'
    DOCS_LANG = 'en'
    DJANGO_VERSION_TO_SCRAPE = '6.0'
    LANG_TO_SCRAPE = 'en'
    DJANGO_DOCS_ROOT_URL = f'{BASE_URL_TO_SCRAPE}/{LANG_TO_SCRAPE}/{DJANGO_VERSION_TO_SCRAPE}'

    def __init__(self):
        self.already_scraped_urls = set()
        self.already_scraped_files = self.find_already_scraped_files()
        logger.info(f'Found {len(self.already_scraped_files)} scraped files on disk already.')
        self.urls_to_scrape = set([self.DJANGO_DOCS_ROOT_URL])

    def dumped_html_path(self):
        return dumped_html_path()

    def find_already_scraped_files(self):
        res = set()
        for file in os.listdir(self.dumped_html_path()):
            if file.endswith(".html"):
                res.add(self.dumped_html_path() / Path(file))
        return res

    def url_to_filepath(self, url: str)->str:
        filename = url.replace('//', '_').replace('/', '_').replace('.', '_').replace(':', '_')
        path = self.dumped_html_path() / Path(filename + '.html')
        return path

    def get_html(self, url)->tuple[str, bool]:
        url_to_scrape = ''

        if not url:
            raise self.BlankUrlException(url)

        if url.startswith('http:'):
            raise self.NonHTTPSPageException(url)
        
        url = url.replace('../', '')

        if not url.startswith('https'):  # relative path to another page
            url_to_scrape = f"{self.DJANGO_DOCS_ROOT_URL}/{url}"
        else:
            url_to_scrape = url

        url_to_scrape = url_to_scrape.split('#')[0]

        self.assert_url_is_not_excluded(url_to_scrape)
        
        filepath = self.url_to_filepath(url_to_scrape)
        if filepath in self.already_scraped_files:
            logger.info(f'URL HTML file already on disk, skipping: {filepath=}')
            with open(filepath, 'r') as f:
                return f.read(), False

        self.assert_en_lang_in_url(url_to_scrape)
        
        self.assert_version_in_url(url_to_scrape)

        if not url_to_scrape:
            raise ValueError

        resp = requests.get(url_to_scrape)
        self.already_scraped_urls.add(url)

        logger.info(f'Scraped: {url=} , {url_to_scrape=}')

        not_found_page_msg="Looks like you followed a bad link. If you think it's our fault, please"
        if not_found_page_msg in resp.text:
            raise self.PageNotFoundException(f"Page not found: {url=}, {url_to_scrape=}")

        with open(filepath, 'w') as f:
            f.write(resp.text)

        logger.info(f'Dumped HTML to file: {filepath}')

        self.already_scraped_files.add(filepath)

        return resp.text, True
    
    def assert_en_lang_in_url(self, url: str):
        page_language = url.split(self.BASE_URL_TO_SCRAPE + '/')[1][:2]
        if page_language != self.LANG_TO_SCRAPE:
            raise self.LanguageNotMatchedException(f'{page_language=} -> {url=}')
        
    def assert_version_in_url(self, url: str):
        page_version = url.split(self.BASE_URL_TO_SCRAPE + '/' + self.LANG_TO_SCRAPE + '/')[1][:3]
        if self.DJANGO_VERSION_TO_SCRAPE not in page_version:
            raise self.VersionNotMatchedException(f'{page_version=} -> {url=}')
        
    def assert_url_is_not_excluded(self, url):
        if not url.startswith(self.BASE_URL_TO_SCRAPE):
                raise self.ExcludedURLException(f'{url=} , {url=}')

    def get_soup(self, resp: str):
        return BeautifulSoup(resp, 'html.parser')
    
    def extract_links(self, soup):
        urls = soup.find_all('a')
        return urls
    
    def extend_urls_to_scrape(self, links):
        for link in links:
            url = link.get('href')
            if url in self.already_scraped_urls:
                logger.info(f'Will not scrape {url} again!')
                continue
            self.urls_to_scrape.add(link.get('href'))
    
    def scrape_all(self):
        breakpoint()
        not_found_pages = set()
        while True:
            url = self.urls_to_scrape.pop()
            try:
                resp, scraped = self.get_html(url)
            except self.Error as e:
                logger.exception(e)
                continue
            except self.PageNotFoundException:
                not_found_pages.add(url)
                continue

            soup = scraper.get_soup(resp)
            links = scraper.extract_links(soup)
            scraper.extend_urls_to_scrape(links)

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


scraper = HTMLScraper()
scraper.scrape_all()
