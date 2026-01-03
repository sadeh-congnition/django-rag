from django.contrib import admin
from .models import EmbeddingModel, EmbedderEval


@admin.register(EmbeddingModel)
class EmbeddingModelAdmin(admin.ModelAdmin):
    list_display = ("name", "url", "created_at", "updated_at")
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
        "description",
        "num_tests",
        "search_times",
        "embedding_time",
        "average_eval_time",
        "eval_scores",
        "avrg_eval_score",
        "created_at",
    )
    list_filter = ("embedding_model", "created_at", "updated_at")
    search_fields = ("name", "description", "embedding_model__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("name", "embedding_model", "description")}),
        (
            "Evaluation Metrics",
            {"fields": ("eval_score", "total_eval_time", "average_eval_time")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("embedding_model")

    def avrg_eval_score(self, obj):
        if obj.eval_scores and isinstance(obj.eval_scores, list):
            return sum(obj.eval_scores) / len(obj.eval_scores) if obj.eval_scores else 0
        return 0
    avrg_eval_score.short_description = "Average Eval Score"
