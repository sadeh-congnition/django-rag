import os
import requests
from pathlib import Path
from rich import print
from loguru import logger
from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from django.db.utils import IntegrityError
from requests.exceptions import HTTPError
from typing import Union

from .models import (
    NotFoundURL,
    Page,
    ScrapedURLsCache,
    URLToVisit,
    URLToVisitCache,
    HREFScraped,
)


scraped_url_cache = ScrapedURLsCache()
urls_to_visit_cache = URLToVisitCache()


class HTMLScraper:
    BASE_URL_TO_SCRAPE = "https://docs.djangoproject.com"
    DOCS_LANG = "en"
    DJANGO_VERSION_TO_SCRAPE = "6.0"
    LANG_TO_SCRAPE = "en"
    DJANGO_DOCS_ROOT_URL = (
        f"{BASE_URL_TO_SCRAPE}/{LANG_TO_SCRAPE}/{DJANGO_VERSION_TO_SCRAPE}"
    )

    def __init__(self, base_url=None, http_client=requests):
        self.http_client = http_client
        if base_url:
            self.first_url_to_scrape = base_url
        else:
            self.first_url_to_scrape = self.DJANGO_DOCS_ROOT_URL

        self.url_to_visit = None

    class StubResponse:
        def __init__(self, url, html):
            self.status_code = 200
            self.text = html
            self.url = url

    def get_html(
        self, url, link
    ) -> tuple[Union[requests.Response, StubResponse], bool, Page]:
        if url in scraped_url_cache.get_all():
            logger.info(f"URL already scraped and in DB, skipping: {url=}")
            page = Page.get_page_by_url(url)
            assert page
            return self.StubResponse(url, page.html_content), False, page

        if url in NotFoundURL.all_not_found_urls():
            logger.info(f"URL previously marked as 404 in DB, skipping: {url=}")
            raise self.PageNotFoundException(f"{url=}")

        logger.info(f"Fetching URL: {url=}")
        resp = self.http_client.get(url, timeout=10)

        if resp.status_code == 404:
            NotFoundURL.objects.get_or_create(url=url)
            breakpoint()

        resp.raise_for_status()

        logger.info(f"Scraped: {url=}")

        not_found_page_msg = (
            "Looks like you followed a bad link. If you think it's our fault, please"
        )
        if not_found_page_msg in resp.text:
            NotFoundURL.objects.get_or_create(url=url)
            raise ValueError(f"Page not found: {url=}")

        page = Page.create(url=url, html_content=resp.text, cache=scraped_url_cache)
        logger.info(f"Saved page to DB: {page=}")

        return resp, True, page

    def assert_en_lang_in_url(self, url: str):
        parts = url.split(self.BASE_URL_TO_SCRAPE + "/")
        if len(parts) < 2:
            raise self.LanguageNotMatchedException(
                f"could not parse language -> {url=}"
            )
        page_language = parts[1].split("/")[0]
        if page_language != self.LANG_TO_SCRAPE:
            raise self.LanguageNotMatchedException(f"{page_language=} -> {url=}")

    def assert_version_in_url(self, url: str):
        parts = url.split(self.BASE_URL_TO_SCRAPE + "/" + self.LANG_TO_SCRAPE + "/")
        if len(parts) < 2:
            raise self.VersionNotMatchedException(f"could not parse version -> {url=}")
        page_version = parts[1].split("/")[0]
        if not page_version.startswith(self.DJANGO_VERSION_TO_SCRAPE):
            raise self.VersionNotMatchedException(f"{page_version=} -> {url=}")

    def assert_url_is_not_excluded(self, url):
        if not url.startswith(self.BASE_URL_TO_SCRAPE):
            raise self.ExcludedURLException(f"{url=} , {url=}")

    def get_soup(self, resp: Union[requests.Response, StubResponse]):
        return BeautifulSoup(resp.text, "html.parser")

    def assert_url_is_valid(self, url: str):
        self.assert_url_is_not_excluded(url)
        self.assert_en_lang_in_url(url)
        self.assert_version_in_url(url)

    def make_full_valid_url(
        self, link, resp: Union[requests.Response, StubResponse]
    ) -> str:
        def remove_hashtag(text: str) -> str:
            return text.split("#")[0]

        url = link.get("href")

        if url == "overview/":
            pass

        if url == "tutorial01/":
            pass
        if url == "../tutorial01/":
            pass
        if url == "../checks/":
            pass

        if not url:
            raise self.BlankUrlException(url)

        if "releases" in url:
            raise self.ExcludedURLException(f"{url=}")

        if not url:
            raise self.BlankUrlException(url)

        elif "contributing@" in url:
            return ""

        elif url.startswith("mailto:"):
            return ""

        elif url.startswith("http://"):
            raise self.NonHTTPSPageException(url)

        elif url.startswith("https://"):  # TestCase1
            self.assert_url_is_valid(url)
            final_url = remove_hashtag(url)

        elif url.startswith("#"):  # TestCase2
            raise self.LinkToCurrentPageException(url)

        elif link.has_attr("class"):  # TestCase3
            if "reference" in link["class"] and "internal" in link["class"]:
                page_url_split = resp.url.split("/")
                if resp.url.endswith("/"):
                    page_url_split.pop()

                url_split = url.split("../")
                for _ in range(url.count("../")):
                    page_url_split.pop()
                    url_split.pop(0)

                page_url_split.append("")

                new_page_url = "/".join(page_url_split)
                new_url = "".join(url_split)
                full_url = urljoin(new_page_url, new_url)
                self.assert_url_is_valid(full_url)
                final_url = remove_hashtag(full_url)

        elif url.strip("/") in {"contents", "intro"}:
            full_url = f"{self.DJANGO_DOCS_ROOT_URL}/{url.lstrip('/')}"
            self.assert_url_is_valid(full_url)
            final_url = remove_hashtag(full_url)

        elif url.startswith("/en/stable/"):
            full_url = f"{self.DJANGO_DOCS_ROOT_URL}/{url.split('/en/stable/')[-1]}"
            self.assert_url_is_valid(full_url)
            final_url = remove_hashtag(full_url)

        elif url.startswith(".."):
            page_url_split = resp.url.split("/")
            if resp.url.endswith("/"):
                page_url_split.pop()

            url_split = url.split("../")
            for _ in range(url.count("../")):
                page_url_split.pop()
                url_split.pop(0)

            page_url_split.append("")

            new_page_url = "/".join(page_url_split)
            new_url = "".join(url_split)
            full_url = urljoin(new_page_url, new_url)
            self.assert_url_is_valid(full_url)
            final_url = remove_hashtag(full_url)

        elif link.has_attr("rel") and "next" in link["rel"]:
            full_url = urljoin(resp.url, url)
            self.assert_url_is_valid(full_url)
            final_url = remove_hashtag(full_url)

        else:
            pass
            raise ValueError(
                f"Could not parse URL: {url=} from page {resp.url=} with link {link}"
            )

        if final_url in to_break:
            pass
            # breakpoint()

        return final_url

    def extract_links(self, soup):
        urls = soup.find_all("a")
        return urls

    def extend_urls_to_scrape(
        self, links, resp: Union[requests.Response, StubResponse], page: Page
    ):
        for link in links:
            if link.get("href"):
                HREFScraped.get_or_create(url=link.get("href"))
            try:
                url = self.make_full_valid_url(link, resp)
            except self.Error as e:
                # logger.exception(e)
                continue

            if not url:
                continue

            self.add_url_to_scrape(page, url, link)

    def add_url_to_scrape(self, page: Page, url, link):
        if url in urls_to_visit_cache.get_all():
            logger.info(f"URLToVisit already in cache, skipping: {url=}")
            return
        try:
            URLToVisit.create(page, url, str(link), urls_to_visit_cache)
        except IntegrityError:
            logger.info(f"URLToVisit already exists in DB, skipping: {url=}")

    def get_url_to_scrape(self) -> URLToVisit:
        obj = URLToVisit.get_one_not_processed()
        if not obj:
            raise self.NoURLsToScrape("No more URLs to scrape")
        return obj

    def scrape_all(self):
        first_url_scraped = False
        while True:
            if not first_url_scraped:
                url = self.first_url_to_scrape
                self.url_to_visit = None
                link = None
                first_url_scraped = True
            else:
                try:
                    self.url_to_visit = self.get_url_to_scrape()
                except self.NoURLsToScrape:
                    break
                url = self.url_to_visit.url
                link = BeautifulSoup(self.url_to_visit.link_element, "html.parser")

            if not url:
                break

            try:
                resp, scraped, page = self.get_html(url, link)
            except self.Error as e:
                # logger.exception(e)
                if self.url_to_visit:
                    self.url_to_visit.mark_processed()
                continue
            except self.PageNotFoundException:
                if self.url_to_visit:
                    self.url_to_visit.mark_processed()
                continue
            except HTTPError as e:
                continue

            logger.info(f"Got HTML for URL: {url=}")

            soup = self.get_soup(resp)
            links = self.extract_links(soup)
            self.extend_urls_to_scrape(links, resp, page)

            if self.url_to_visit:
                self.url_to_visit.mark_processed()

            if scraped:
                pytest_run = os.getenv("PYTEST_CURRENT_TEST")
                if pytest_run:
                    x = 0
                else:
                    x = 2
                logger.info(f"Going to sleep {x} seconds...")
                sleep(x)

    class Error(Exception):
        pass

    class NoURLsToScrape(Error):
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

    class AlreadyScrapedURLException(Exception):
        pass


to_break = {"https://docs.djangoproject.com/en/6.0/ref/contrib/django-admin/"}
