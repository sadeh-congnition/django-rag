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
