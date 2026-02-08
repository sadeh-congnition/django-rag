from django.db import models
from chromadb import EmbeddingFunction
from embedding_generator.using_lm_studio import get_embeddings


class EmbeddingModel(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id: int

    class Meta:
        verbose_name = "Embedding Model"
        verbose_name_plural = "Embedding Models"

    def __str__(self):
        return f"{self.id}: {self.name}"

    @classmethod
    def create_defaults(cls):
        cls.objects.get_or_create(
            name="text-embedding-granite-embedding-30m-english",
            url="https://huggingface.co/lmstudio-community/granite-embedding-30m-english-GGUF",
        )
        cls.objects.get_or_create(
            name="text-embedding-granite-embedding-125m-english",
            url="https://huggingface.co/lmstudio-community/granite-embedding-125m-english-GGUF",
        )
        cls.objects.get_or_create(
            name="text-embedding-embeddinggemma-300m",
            url="https://huggingface.co/unsloth/embeddinggemma-300m-GGUF",
        )
        cls.objects.get_or_create(
            name="text-embedding-granite-embedding-278m-multilingual",
            url="https://huggingface.co/lmstudio-community/granite-embedding-278m-multilingual-GGUF",
        )
        cls.objects.get_or_create(
            name="text-embedding-qwen3-embedding-0.6b",
            url="https://huggingface.co/Qwen/Qwen3-Embedding-0.6B-GGUF",
        )
        cls.objects.get_or_create(
            name="text-embedding-qwen3-embedding-4b",
            url="https://huggingface.co/Qwen/Qwen3-Embedding-4B-GGUF",
        )
        cls.objects.get_or_create(
            name="text-embedding-qwen3-embedding-8b",
            url="https://huggingface.co/Qwen/Qwen3-Embedding-8B-GGUF",
        )
        cls.objects.get_or_create(
            name="granite-embedding-107m-multilingual-GGUF",
            url="https://huggingface.co/lmstudio-community/granite-embedding-107m-multilingual-GGUF",
        )
        cls.objects.get_or_create(
            name="jina-embeddings-v4-text-retrieval-GGUF",
            url="https://huggingface.co/jinaai/jina-embeddings-v4-text-retrieval-GGUF",
        )
        cls.objects.get_or_create(
            name="All-MiniLM-L6-v2-Embedding-GGUF",
            url="https://huggingface.co/second-state/All-MiniLM-L6-v2-Embedding-GGUF",
        )
        cls.objects.get_or_create(
            name="jina-code-embeddings-1.5b-GGUF",
            url="https://huggingface.co/jinaai/jina-code-embeddings-1.5b-GGUF",
        )
        cls.objects.get_or_create(
            name="jina-embeddings-v4-text-code-GGUF",
            url="https://huggingface.co/jinaai/jina-embeddings-v4-text-code-GGUF",
        )
        cls.objects.get_or_create(
            name="jina-embeddings-v2-base-code-GGUF",
            url="https://huggingface.co/second-state/jina-embeddings-v2-base-code-GGUF",
        )

    @classmethod
    def embed_funcs(cls) -> list["EmbeddingModelKlass"]:
        return [EmbeddingModelKlass(row.name) for row in cls.objects.all()]

    @classmethod
    def embedding_function(cls, id: int):
        row = cls.objects.get(id=id)
        return EmbeddingModelKlass(row.name)


class EmbeddingModelKlass(EmbeddingFunction):
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    def __call__(self, input):
        res = []
        for text in input:
            emb = get_embeddings(self._name, text)
            assert emb
            res.append(emb)
        return res


class MetricConfig(models.Model):
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id: int

    class Meta:
        verbose_name = "Metric Configuration"
        verbose_name_plural = "Metric Configurations"

    def __str__(self):
        return f"Config {self.id}"

    def num_tests(self):
        return self.content["metric"]["num_tests"]


class EmbedderPerformance(models.Model):
    embedding_model = models.ForeignKey(
        EmbeddingModel, on_delete=models.CASCADE, null=True, blank=True
    )
    metric_config = models.ForeignKey(
        MetricConfig, on_delete=models.CASCADE, null=True, blank=True
    )
    search_time = models.FloatField()
    embedding_time = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id: int

    class Meta:
        verbose_name = "Embedder Performance Details"
        verbose_name_plural = "Embedder Performance Details"

    def __str__(self):
        return f"Config {self.id}"


class EmbedderEval(models.Model):
    embedding_model = models.ForeignKey(
        EmbeddingModel, on_delete=models.CASCADE, related_name="evaluations"
    )
    chunk_config = models.ForeignKey(
        "chunking.ChunkConfig",
        on_delete=models.CASCADE,
        related_name="embedder_evals",
        blank=True,
        null=True,
    )
    metric_config = models.ForeignKey(
        MetricConfig,
        on_delete=models.CASCADE,
        related_name="evaluations",
        blank=True,
        null=True,
    )
    embedder_performance = models.ForeignKey(
        EmbedderPerformance,
        on_delete=models.CASCADE,
        related_name="evaluations",
        blank=True,
        null=True,
    )
    sample = models.ForeignKey(
        "Sample",
        on_delete=models.SET_NULL,
        related_name="embedder_evals",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"

    def __str__(self):
        return f"{self.name} - {self.embedding_model.name}"


class BadResult(models.Model):
    embedder_eval = models.ForeignKey(
        EmbedderEval, on_delete=models.CASCADE, related_name="bad_results"
    )
    content = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bad Result"
        verbose_name_plural = "Bad Results"

    def __str__(self):
        return f"Bad Result for {self.embedder_eval.name}"


class Sample(models.Model):
    chunk_description_ids = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id: int

    class Meta:
        verbose_name = "Sample"
        verbose_name_plural = "Samples"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Sample {self.id}"
