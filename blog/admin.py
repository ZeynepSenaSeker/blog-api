from django.contrib import admin
from .models import Category, Post


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'published_at', 'is_indexable')
    list_filter = ('status', 'category', 'is_indexable')
    search_fields = ('title', 'content', 'focus_keyword')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    actions = ['publish_selected']
    fieldsets = (
        ('Content', {
            'fields': ('title', 'slug', 'excerpt', 'content', 'cover_image_url', 'cover_image_alt'),
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'focus_keyword', 'canonical_url', 'is_indexable'),
            'description': 'Meta title ≤ 60 characters, meta description ≤ 160.',
        }),
        ('Publishing', {
            'fields': ('author', 'category', 'status', 'published_at'),
        }),
    )

    def get_queryset(self, request):
        # Avoid the N+1 in the list page.
        return super().get_queryset(request).select_related('author', 'category')

    @admin.action(description='Publish selected posts')
    def publish_selected(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{updated} post(s) published.')
