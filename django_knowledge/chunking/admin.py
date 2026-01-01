from django.contrib import admin
from .models import Chunk, ChunkDescription


@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ('python_file', 'updated_at', 'created_at')
    list_filter = ('python_file__project', 'created_at', 'updated_at')
    search_fields = ('content', 'python_file__module_path', 'python_file__project__name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('python_file', 'python_file__project')


@admin.register(ChunkDescription)
class ChunkDescriptionAdmin(admin.ModelAdmin):
    list_display = ('chunk', 'description_preview', 'created_at')
    list_filter = ('chunk__python_file__project', 'created_at')
    search_fields = ('description', 'chunk__content', 'chunk__python_file__module_path')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    def description_preview(self, obj):
        return obj.description[:100] + '...' if len(obj.description) > 100 else obj.description
    description_preview.short_description = 'Description'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'chunk', 
            'chunk__python_file', 
            'chunk__python_file__project'
        )
