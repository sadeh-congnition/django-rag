from django.db import models
from synthetic_data_generator.models import PythonFile


class Chunk(models.Model):
    python_file = models.ForeignKey(PythonFile, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chunk"
        verbose_name_plural = "Chunks"
        ordering = ['updated_at']

    def __str__(self):
        return f"Chunk from {self.python_file.module_path} ({self.updated_at})"

    def previous(self):
        """Return the previous chunk for the same PythonFile based on updated_at."""
        return Chunk.objects.filter(
            python_file=self.python_file,
            updated_at__lt=self.updated_at
        ).order_by('-updated_at').first()

    def next(self):
        """Return the next chunk for the same PythonFile based on updated_at."""
        return Chunk.objects.filter(
            python_file=self.python_file,
            updated_at__gt=self.updated_at
        ).order_by('updated_at').first()


class ChunkDescription(models.Model):
    chunk = models.ForeignKey(Chunk, on_delete=models.CASCADE, related_name='descriptions')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Chunk Description"
        verbose_name_plural = "Chunk Descriptions"
        ordering = ['created_at']

    def __str__(self):
        return f"Description for {self.chunk} - {self.description[:50]}..."
