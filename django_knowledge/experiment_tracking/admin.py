from django.contrib import admin
import json
from django.utils.safestring import mark_safe
from .models import (
    EmbeddingModel,
    EmbedderEval,
    BadResult,
    MetricConfig,
    EmbedderPerformance,
    Sample,
)


@admin.register(EmbeddingModel)
class EmbeddingModelAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("name", "url")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("name", "url")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(EmbedderEval)
class EmbedderEvalAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "embedding_model",
        "sample",
        "chunk_config",
        "score_percentage",
        "metric_config_pretty",
        "embedder_performance_pretty",
        "description",
        "created_at",
    )
    list_filter = (
        "embedding_model",
        "chunk_config",
        "metric_config",
        "embedder_performance",
        "created_at",
        "updated_at",
    )
    search_fields = ("name", "description", "embedding_model__name")
    readonly_fields = (
        "created_at",
        "updated_at",
        "metric_config_pretty",
        "embedder_performance_pretty",
    )
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("name", "embedding_model", "description")}),
        (
            "Configuration",
            {
                "fields": (
                    "chunk_config",
                    "metric_config_pretty",
                    "embedder_performance_pretty",
                )
            },
        ),
        (
            "Results",
            {"fields": ("score",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "embedding_model",
                "chunk_config",
                "metric_config",
                "embedder_performance",
            )
        )

    def metric_config_pretty(self, obj):
        if obj.metric_config and obj.metric_config.content:
            content_str = json.dumps(
                obj.metric_config.content, indent=2, ensure_ascii=False
            )
            return mark_safe(f"<pre>{content_str}</pre>")
        return "No metric config"

    metric_config_pretty.short_description = "Metric Config"

    def embedder_performance_pretty(self, obj):
        if obj.embedder_performance:
            perf_data = {
                "search_time": obj.embedder_performance.search_time,
                "embedding_time": obj.embedder_performance.embedding_time,
            }
            if obj.embedder_performance.embedding_model:
                perf_data["embedding_model"] = (
                    obj.embedder_performance.embedding_model.name
                )
            content_str = json.dumps(perf_data, indent=2, ensure_ascii=False)
            return mark_safe(f"<pre>{content_str}</pre>")
        return "No performance data"

    embedder_performance_pretty.short_description = "Embedder Performance"

    def score_percentage(self, obj):
        num_tests = obj.metric_config.num_tests()
        percentage = (obj.score / num_tests) * 100
        return f"{percentage:.1f}% ({obj.score}/{num_tests})"

    score_percentage.short_description = "Score"


@admin.register(BadResult)
class BadResultAdmin(admin.ModelAdmin):
    list_display = ("embedder_eval", "content_preview", "created_at", "updated_at")
    list_filter = (
        "embedder_eval__embedding_model",
        "embedder_eval__name",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "embedder_eval__name",
        "embedder_eval__embedding_model__name",
        "content",
    )
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("embedder_eval",)}),
        (
            "Content",
            {"fields": ("content",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("embedder_eval__embedding_model")
        )

    def content_preview(self, obj):
        import json

        if obj.content:
            # Extract key information for preview
            content_str = f"Correct: {obj.content.get('correct_chunk_id', 'N/A')}, "
            content_str += f"Returned: {obj.content.get('returned_chunk_id', 'N/A')}"
            return content_str
        return "No content"

    content_preview.short_description = "Content Preview"


@admin.register(Sample)
class SampleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "chunk_description_ids_preview",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("chunk_description_ids",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def chunk_description_ids_preview(self, obj):
        if obj.chunk_description_ids:
            content_str = json.dumps(obj.chunk_description_ids, indent=2)
            if len(content_str) > 200:
                content_str = content_str[:200] + "..."
            return mark_safe(f"<pre>{content_str}</pre>")
        return "No chunk description ids"

    chunk_description_ids_preview.short_description = "Chunk Description Ids"


@admin.register(MetricConfig)
class MetricConfigAdmin(admin.ModelAdmin):
    list_display = ("id", "content_preview", "created_at", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = ("content",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("content",)}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def content_preview(self, obj):
        if obj.content:
            # Create a readable preview of the JSON content
            content_str = json.dumps(obj.content, indent=2, ensure_ascii=False)
            if len(content_str) > 200:
                content_str = content_str[:200] + "..."
            return mark_safe(f"<pre>{content_str}</pre>")
        return "No content"

    content_preview.short_description = "Content Preview"


@admin.register(EmbedderPerformance)
class EmbedderPerformanceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "search_time",
        "embedding_time",
        "content_preview",
        "created_at",
        "updated_at",
    )
    list_filter = ("created_at", "updated_at")
    search_fields = ("content",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("search_time", "embedding_time")}),
        (
            "Content",
            {"fields": ("content",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def content_preview(self, obj):
        if obj.content:
            # Create a readable preview of the JSON content
            content_str = json.dumps(obj.content, indent=2, ensure_ascii=False)
            if len(content_str) > 200:
                content_str = content_str[:200] + "..."
            return mark_safe(f"<pre>{content_str}</pre>")
        return "No content"

    content_preview.short_description = "Content Preview"
