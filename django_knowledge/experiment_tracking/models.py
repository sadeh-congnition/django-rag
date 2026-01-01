from django.db import models


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


class Evaluation(models.Model):
    embedding_model = models.ForeignKey(
        EmbeddingModel, 
        on_delete=models.CASCADE, 
        related_name='evaluations'
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    eval_time = models.DateTimeField()
    model_name = models.CharField(max_length=255)
    eval_score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evaluation"
        verbose_name_plural = "Evaluations"
        ordering = ['-eval_time']

    def __str__(self):
        return f"{self.name} - {self.embedding_model.name}"
