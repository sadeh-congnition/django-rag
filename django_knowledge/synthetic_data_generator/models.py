from django.db import models


class Project(models.Model):
    name = models.CharField(max_length=100)
    root_path = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name}"


class PythonFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    content = models.TextField()
    module_path = models.CharField(max_length=500, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Python File"
        verbose_name_plural = "Python Files"

    def __str__(self):
        return f"{self.project.name} - {self.module_path}"


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
