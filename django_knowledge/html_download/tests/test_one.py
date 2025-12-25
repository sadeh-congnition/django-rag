from typing import Type
from dataclasses import dataclass

from pytest import fixture

from html_download.models import NotFoundURL, URLToVisit, Page
from html_download.html_scraper import HTMLScraper


@dataclass()
class TestHTTPClient:
    fetch_url: str
    fetched_url: str
    text: str
    status_code: int = 200

    @property
    def url(self):
        return self.fetched_url

    def get(self, url, timeout=10):
        return self

    def raise_for_status(self):
        pass


@fixture
def http_client(db) -> Type:
    return TestHTTPClient


@fixture
def base_url():
    return HTMLScraper.BASE_URL_TO_SCRAPE


def reference_internal_a_tag(href: str) -> str:
    return f"""<a class="reference internal" href={href}><span class="std std-ref">spatial database template</span></a>"""


class TestCase1:
    @fixture
    def full_href(self):
        return "https://docs.djangoproject.com/en/6.0/ref/contrib/gis/install/geolibs/"

    def test_link_starting_with_https(self, http_client, base_url, full_href):
        text = reference_internal_a_tag(full_href)
        http_client = TestHTTPClient(
            fetch_url=base_url,
            fetched_url=base_url,
            text=text,
        )
        scraper = HTMLScraper(base_url=base_url, http_client=http_client)
        scraper.scrape_all()

        assert NotFoundURL.objects.count() == 0
        assert URLToVisit.objects.count() == 1
        assert Page.objects.count() == 2

        p1 = Page.objects.get(url=base_url)
        assert p1.html_content
        assert p1.html_content_hash
        assert p1.date_created
        assert p1.date_updated

        p2 = Page.objects.get(url=full_href)
        assert p2.html_content
        assert p2.html_content_hash
        assert p2.date_created
        assert p2.date_updated


class TestCase2:
    @fixture
    def current_page_elem(self):
        return "#blah"

    def test_link_to_current_page(self, http_client, base_url, current_page_elem):
        text = reference_internal_a_tag(current_page_elem)
        http_client = TestHTTPClient(
            fetch_url=base_url,
            fetched_url=base_url,
            text=text,
        )
        scraper = HTMLScraper(base_url=base_url, http_client=http_client)
        scraper.scrape_all()

        assert NotFoundURL.objects.count() == 0
        assert URLToVisit.objects.count() == 0
        assert Page.objects.count() == 1

        p1 = Page.objects.get(url=base_url)
        assert p1.html_content
        assert p1.html_content_hash
        assert p1.date_created
        assert p1.date_updated


class TestCase3:
    @fixture
    def one_level_up(self):
        return "../blah/"

    def test_relative_one_level_up_link(self, http_client, one_level_up):
        base_url = (
            "https://docs.djangoproject.com/en/6.0/ref/contrib/gis/install/geolibs/"
        )
        text = reference_internal_a_tag(one_level_up)
        http_client = TestHTTPClient(
            fetch_url=base_url,
            fetched_url=base_url,
            text=text,
        )
        scraper = HTMLScraper(base_url=base_url, http_client=http_client)
        scraper.scrape_all()

        correct_constructed_url = (
            "https://docs.djangoproject.com/en/6.0/ref/contrib/gis/install/blah/"
        )

        assert NotFoundURL.objects.count() == 0
        assert URLToVisit.objects.count() == 1
        assert Page.objects.count() == 2

        url = URLToVisit.objects.first()
        assert url.url == correct_constructed_url

        p1 = Page.objects.get(url=base_url)
        assert p1.html_content
        assert p1.html_content_hash
        assert p1.date_created
        assert p1.date_updated

        p2 = Page.objects.get(url=correct_constructed_url)
        assert p2.html_content
        assert p2.html_content_hash
        assert p2.date_created
        assert p2.date_updated

    @fixture
    def two_levels_up(self):
        return "../../blah/"

    def test_relative_two_levels_up_link(self, http_client):
        base_url = "https://docs.djangoproject.com/en/6.0/ref/contrib/admin/index"
        fetched_url = "https://docs.djangoproject.com/en/6.0/ref/contrib/admin/"
        text = """<a class="reference internal" href="../../django-admin/#django-admin-startproject"><code class="xref std std-djadmin docutils literal notranslate"><span class="pre">startproject</span></code></a>"""
        http_client = TestHTTPClient(
            fetch_url=base_url,
            fetched_url=fetched_url,
            text=text,
        )
        scraper = HTMLScraper(base_url=base_url, http_client=http_client)
        scraper.scrape_all()

        assert NotFoundURL.objects.count() == 0
        assert URLToVisit.objects.count() == 1
        assert Page.objects.count() == 2

        correct_constructed_url = (
            "https://docs.djangoproject.com/en/6.0/ref/django-admin/"
        )

        url = URLToVisit.objects.first()
        assert url.url == correct_constructed_url

        p1 = Page.objects.get(url=base_url)
        assert p1.html_content
        assert p1.html_content_hash
        assert p1.date_created
        assert p1.date_updated

        p2 = Page.objects.get(url=correct_constructed_url)
        assert p2.html_content
        assert p2.html_content_hash
        assert p2.date_created
        assert p2.date_updated
