from django.contrib import admin
from .models import Page, NotFoundURL, URLToVisit, HREFScraped


@admin.register(HREFScraped)
class HREFScrapedAdmin(admin.ModelAdmin):
    list_display = ("href_url",)
    search_fields = ("href_url",)


@admin.register(URLToVisit)
class URLToVisitAdmin(admin.ModelAdmin):
    list_display = ("url", "processed", "date_added", "date_updated")
    search_fields = ("url",)
    list_filter = ("processed",)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ("url", "date_created", "date_updated")
    search_fields = ("url",)


@admin.register(NotFoundURL)
class NotFoundURLAdmin(admin.ModelAdmin):
    list_display = ("url",)
    search_fields = ("url",)
