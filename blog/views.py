from django.db.models import Q
from django.shortcuts import get_object_or_404
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    ListCreateAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .models import Category, Post, PostStatus
from .permissions import IsAuthorOrReadOnly
from .responses import APIResponse
from .serializers import (
    CategorySerializer,
    PostDetailSerializer,
    PostListSerializer,
    PostSitemapSerializer,
    PostWriteSerializer,
)


class CategoryListView(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary='List categories',
        operation_description='Retrieve all topic categories.',
        tags=['Categories'],
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return APIResponse(data=response.data, message='Categories retrieved.')


class PostListCreateView(ListCreateAPIView):
    """GET — published posts (public), plus your own drafts when signed in.
    POST — create a post as the signed-in user.
    """

    def get_permissions(self):
        return [IsAuthenticated()] if self.request.method == 'POST' else [AllowAny()]

    def get_serializer_class(self):
        return PostWriteSerializer if self.request.method == 'POST' else PostListSerializer

    def get_queryset(self):
        queryset = Post.objects.with_relations()
        user = self.request.user
        if user.is_authenticated:
            queryset = queryset.filter(Q(status=PostStatus.PUBLISHED) | Q(author=user))
        else:
            queryset = queryset.filter(status=PostStatus.PUBLISHED)

        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(excerpt__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @swagger_auto_schema(
        operation_summary='List posts',
        operation_description='Published posts, plus your own drafts when signed in.',
        manual_parameters=[
            openapi.Parameter(
                'category',
                openapi.IN_QUERY,
                description='Category slug filter',
                type=openapi.TYPE_STRING,
            ),
            openapi.Parameter(
                'search',
                openapi.IN_QUERY,
                description='Search titles and excerpts',
                type=openapi.TYPE_STRING,
            ),
        ],
        tags=['Posts'],
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return APIResponse(data=response.data, message='Posts retrieved.')

    @swagger_auto_schema(
        operation_summary='Create post',
        operation_description='Create a new post as the authenticated user.',
        request_body=PostWriteSerializer,
        tags=['Posts'],
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return APIResponse(
            data=response.data,
            message='Post created.',
            status=status.HTTP_201_CREATED,
        )


class PostDetailView(RetrieveUpdateDestroyAPIView):
    lookup_field = 'slug'
    permission_classes = [IsAuthorOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ('PUT', 'PATCH'):
            return PostWriteSerializer
        return PostDetailSerializer

    def get_queryset(self):
        queryset = Post.objects.with_relations()
        user = self.request.user
        if user.is_authenticated:
            return queryset.filter(Q(status=PostStatus.PUBLISHED) | Q(author=user))
        return queryset.filter(status=PostStatus.PUBLISHED)

    @swagger_auto_schema(
        operation_summary='Get post details',
        operation_description='Retrieve full post details including SEO metadata by slug.',
        tags=['Posts'],
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return APIResponse(data=response.data, message='Post retrieved.')

    @swagger_auto_schema(
        operation_summary='Partially update post',
        operation_description='Update selected post fields. Only author allowed.',
        request_body=PostWriteSerializer,
        tags=['Posts'],
    )
    def patch(self, request, *args, **kwargs):
        response = super().patch(request, *args, **kwargs)
        return APIResponse(data=response.data, message='Post updated.')

    @swagger_auto_schema(
        operation_summary='Update post',
        operation_description='Replace post fields. Only author allowed.',
        request_body=PostWriteSerializer,
        tags=['Posts'],
    )
    def put(self, request, *args, **kwargs):
        response = super().put(request, *args, **kwargs)
        return APIResponse(data=response.data, message='Post updated.')

    @swagger_auto_schema(
        operation_summary='Delete post',
        operation_description='Delete post permanently. Only author allowed.',
        tags=['Posts'],
    )
    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return APIResponse(status=status.HTTP_204_NO_CONTENT)


class PostPublishView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary='Publish post',
        operation_description='Publish a draft post. Only author allowed.',
        responses={
            200: 'Post published successfully.',
            403: 'You can only publish your own posts.',
            409: 'This post is already published.',
        },
        tags=['Posts'],
    )
    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug)
        if post.author_id != request.user.id:
            return APIResponse(
                errors={'non_field_errors': ['You can only publish your own posts.']},
                status=status.HTTP_403_FORBIDDEN,
            )
        if post.status == PostStatus.PUBLISHED:
            return APIResponse(
                errors={'non_field_errors': ['This post is already published.']},
                status=status.HTTP_409_CONFLICT,
            )
        post.publish()
        return APIResponse(
            data=PostDetailSerializer(post).data,
            message='Post published.',
        )


class PostSitemapView(ListAPIView):
    """Slugs and timestamps for every indexable published post — powers sitemap.xml."""
    permission_classes = [AllowAny]
    serializer_class = PostSitemapSerializer

    def get_queryset(self):
        return Post.objects.published().indexable().only('slug', 'updated_at')

    @swagger_auto_schema(
        operation_summary='Get post sitemap entries',
        operation_description='Slugs and timestamps for every indexable published post.',
        tags=['SEO'],
    )
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        return APIResponse(data=response.data, message='Sitemap entries retrieved.')
