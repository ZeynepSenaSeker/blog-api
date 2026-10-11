from django.contrib.auth.models import User
from rest_framework import serializers
from .models import Category, Post


class AuthorSerializer(serializers.ModelSerializer):
    """Embedded author info. Deliberately never includes email."""
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'full_name']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description']
        read_only_fields = ['id', 'slug']


class PostListSerializer(serializers.ModelSerializer):
    """Small payload for the blog index — no article body."""
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    reading_time_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'cover_image_url',
            'cover_image_alt',
            'author',
            'category',
            'status',
            'published_at',
            'reading_time_minutes',
        ]


class PostDetailSerializer(serializers.ModelSerializer):
    """Everything an article page needs, including all the SEO fields."""
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    seo_title = serializers.CharField(read_only=True)
    seo_description = serializers.CharField(read_only=True)
    reading_time_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'title',
            'slug',
            'excerpt',
            'content',
            'cover_image_url',
            'cover_image_alt',
            'seo_title',
            'seo_description',
            'canonical_url',
            'is_indexable',
            'author',
            'category',
            'status',
            'published_at',
            'updated_at',
            'reading_time_minutes',
        ]


class PostWriteSerializer(serializers.ModelSerializer):
    """Accepts input for create and update. `author` is never in here — it
    comes from the logged-in user, not the request body.
    """
    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Post
        fields = [
            'title',
            'excerpt',
            'content',
            'cover_image_url',
            'cover_image_alt',
            'meta_title',
            'meta_description',
            'focus_keyword',
            'canonical_url',
            'is_indexable',
            'category_id',
            'status',
        ]

    def validate_title(self, value):
        value = value.strip()
        if len(value) < 10:
            raise serializers.ValidationError(
                'Title must be at least 10 characters — short titles rank poorly.'
            )
        return value

    def validate_meta_description(self, value):
        if value and len(value) > 160:
            raise serializers.ValidationError(
                'Meta description should be 160 characters or fewer.'
            )
        return value

    def validate(self, attrs):
        status = attrs.get('status', getattr(self.instance, 'status', 'draft'))
        content = attrs.get('content', getattr(self.instance, 'content', ''))
        if status == 'published' and len(content.split()) < 100:
            raise serializers.ValidationError({
                'content': ['Published articles need at least 100 words.'],
            })
        return attrs

    def create(self, validated_data):
        from django.utils.text import slugify
        category_id = validated_data.pop('category_id', None)
        if category_id:
            try:
                validated_data['category'] = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                raise serializers.ValidationError({'category_id': ['Category not found.']})

        validated_data['slug'] = self._unique_slug(slugify(validated_data['title']))
        return super().create(validated_data)

    @staticmethod
    def _unique_slug(base):
        slug, suffix = base, 2
        while Post.objects.filter(slug=slug).exists():
            slug = f'{base}-{suffix}'
            suffix += 1
        return slug


class PostSitemapSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ['slug', 'updated_at']
