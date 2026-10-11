import uuid
from django.conf import settings
from django.db import models
from django.utils.text import slugify


class PostStatus(models.TextChoices):
    DRAFT = 'draft', 'Draft'
    PUBLISHED = 'published', 'Published'
    ARCHIVED = 'archived', 'Archived'


class Category(models.Model):
    """A topic grouping, e.g. 'Rehabilitation' or 'Exercise Science'."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        return super().save(*args, **kwargs)


class PostQuerySet(models.QuerySet):
    def published(self):
        return self.filter(status=PostStatus.PUBLISHED, published_at__isnull=False)

    def indexable(self):
        return self.filter(is_indexable=True)

    def by_category(self, slug):
        return self.filter(category__slug=slug)

    def with_relations(self):
        return self.select_related('author', 'category')


class PostManager(models.Manager.from_queryset(PostQuerySet)):
    pass


class Post(models.Model):
    """A blog article."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # ── Content ──
    title = models.CharField(max_length=200)
    slug = models.SlugField(
        max_length=220,
        unique=True,
        help_text="The URL. Don't change it after publishing — you'd lose the ranking.",
    )
    excerpt = models.CharField(
        max_length=300,
        blank=True,
        default='',
        help_text='Short summary shown in listings.',
    )
    content = models.TextField()
    cover_image_url = models.URLField(blank=True, default='')
    cover_image_alt = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Describe the image. Required for accessibility and image search.',
    )

    # ── SEO ──
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        default='',
        help_text='Shown as the search result title. Falls back to the post title.',
    )
    meta_description = models.CharField(
        max_length=170,
        blank=True,
        default='',
        help_text='Shown under the title in search results. Falls back to the excerpt.',
    )
    focus_keyword = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text='The phrase this article is meant to rank for.',
    )
    canonical_url = models.URLField(
        blank=True,
        default='',
        help_text='Set only if this content was originally published elsewhere.',
    )
    is_indexable = models.BooleanField(
        default=True,
        help_text='Uncheck to tell search engines not to index this page.',
    )

    # ── Relations ──
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
    )

    # ── State ──
    status = models.CharField(
        max_length=20,
        choices=PostStatus.choices,
        default=PostStatus.DRAFT,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostManager()

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status'], name='idx_post_status'),
            models.Index(fields=['-published_at'], name='idx_post_published'),
        ]

    def __str__(self):
        return self.title

    def publish(self):
        from django.utils import timezone
        if self.status == PostStatus.PUBLISHED:
            return self
        self.status = PostStatus.PUBLISHED
        self.published_at = timezone.now()
        self.save(update_fields=['status', 'published_at', 'updated_at'])
        return self

    @property
    def seo_title(self):
        return self.meta_title or self.title

    @property
    def seo_description(self):
        return self.meta_description or self.excerpt

    @property
    def reading_time_minutes(self):
        words = len(self.content.split())
        return max(1, round(words / 200))