from django.contrib import admin
from .models import Roadmap, RoadmapItem, Resource


class RoadmapItemInline(admin.TabularInline):
    model = RoadmapItem
    extra = 0
    readonly_fields = ('id',)


class ResourceInline(admin.TabularInline):
    model = Resource
    extra = 0
    readonly_fields = ('id',)


@admin.register(Roadmap)
class RoadmapAdmin(admin.ModelAdmin):
    list_display = ('report', 'generated_by', 'created_at')
    list_filter = ('generated_by', 'created_at')
    search_fields = ('report__user__email',)
    readonly_fields = ('id', 'created_at')
    ordering = ('-created_at',)
    inlines = [RoadmapItemInline]


@admin.register(RoadmapItem)
class RoadmapItemAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'week_number', 'roadmap')
    list_filter = ('week_number',)
    search_fields = ('skill_name', 'description')
    readonly_fields = ('id',)
    ordering = ['week_number']
    inlines = [ResourceInline]


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'platform', 'resource_type', 'roadmap_item')
    list_filter = ('platform', 'resource_type')
    search_fields = ('title', 'url')
    readonly_fields = ('id',)
