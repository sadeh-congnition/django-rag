from django.contrib import admin
from .models import Project, PythonFile


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'root_path', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'root_path')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(PythonFile)
class PythonFileAdmin(admin.ModelAdmin):
    list_display = ('module_path', 'project', 'updated_at')
    list_filter = ('project', 'created_at', 'updated_at')
    search_fields = ('module_path', 'project__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('project', 'module_path')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project')
