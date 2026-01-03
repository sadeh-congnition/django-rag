from django.db import models
from chromadb import EmbeddingFunction
from embedding_generator.using_lm_studio import get_embeddings


class EmbeddingModel(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Embedding Model"
        verbose_name_plural = "Embedding Models"

    def __str__(self):
        return self.name

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


class EmbeddingModelKlass(EmbeddingFunction):
    def __init__(self, name):
        self._name = name

    def name(self):
        return self._name

    def __call__(self, input):
        res = []
        for text in input:
            res.append(get_embeddings(self._name, text))
        return res


class EmbedderEval(models.Model):
    embedding_model = models.ForeignKey(
        EmbeddingModel, on_delete=models.CASCADE, related_name="evaluations"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    num_tests = models.JSONField()
    search_times = models.JSONField()
    embedding_time = models.FloatField()
    average_eval_time = models.FloatField()
    eval_scores = models.JSONField()
    average_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"

    def __str__(self):
        return f"{self.name} - {self.embedding_model.name}"
