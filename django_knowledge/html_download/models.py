from django.db import models
import hashlib
from dataclasses import dataclass


class NotFoundURL(models.Model):
    url = models.URLField(unique=True)

    def __str__(self):
        return self.url

    @classmethod
    def all_not_found_urls(cls):
        return [obj.url for obj in cls.objects.all()]


class Page(models.Model):
    url = models.URLField(unique=True)
    html_content = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    html_content_hash = models.CharField(max_length=512, blank=True, null=True)
    cleaned_text = models.TextField(blank=True, null=True)
    filepath: str
    html_content: str

    def __str__(self):
        return self.url

    def add_extracted_text(self, text):
        self.cleaned_text = text
        self.save()

    @classmethod
    def get_page_by_url(cls, url):
        try:
            return cls.objects.get(url=url)
        except cls.DoesNotExist:
            return None

    @classmethod
    def all_scraped_urls(cls):
        return {obj.url for obj in cls.objects.all()}

    @classmethod
    def create(cls, url: str, html_content: str, cache):
        h = hashlib.new("sha256")
        h.update(html_content.encode("utf-8"))
        hash = h.hexdigest()
        page = cls(
            url=url,
            html_content=html_content,
            html_content_hash=hash,
        )
        page.save()
        cache.invalidated = True
        return page


@dataclass
class ScrapedURLsCache:
    invalidated: bool = True

    def get_all(self):
        if self.invalidated:
            self.cached_urls = Page.all_scraped_urls()
            self.invalidated = False
        return self.cached_urls


class URLToVisit(models.Model):
    source_page = models.ForeignKey(
        Page, on_delete=models.CASCADE, related_name="url_links"
    )
    date_added = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    url = models.URLField(unique=True)
    link_element = models.TextField()
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.url

    @classmethod
    def create(cls, source_page: Page, url: str, link: str, cache):
        cache.invalidated = True
        obj = cls.objects.create(source_page=source_page, url=url, link_element=link)
        return obj

    def mark_processed(self):
        self.processed = True
        self.save()

    @classmethod
    def all(cls):
        return {elem.url for elem in cls.objects.all()}

    @classmethod
    def get_one_not_processed(cls):
        return cls.objects.filter(processed=False).first()


@dataclass
class URLToVisitCache:
    invalidated: bool = True

    def get_all(self):
        if self.invalidated:
            self.cached_urls = URLToVisit.all()
            self.invalidated = False
        return self.cached_urls


class HREFScraped(models.Model):
    href_url = models.TextField()

    @classmethod
    def get_or_create(cls, url: str):
        cls.objects.get_or_create(href_url=url)

