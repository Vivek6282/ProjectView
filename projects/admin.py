from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'status', 'priority', 'deadline', 'is_overdue')
    list_filter = ('category', 'status', 'priority')
    search_fields = ('title', 'details')
    date_hierarchy = 'deadline'
    readonly_fields = ('created_at', 'updated_at', 'completed_at')
    fieldsets = (
        ('Core Details', {
            'fields': ('title', 'category', 'details', 'created_by')
        }),
        ('Planning & Status', {
            'fields': ('deadline', 'status', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )
