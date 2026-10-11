from django.urls import path
from .views import (
    CategoryListView,
    PostDetailView,
    PostListCreateView,
    PostPublishView,
    PostSitemapView,
)

urlpatterns = [
    path('categories/', CategoryListView.as_view(), name='category-list'),
    path('posts/', PostListCreateView.as_view(), name='post-list'),
    path('posts/<slug:slug>/', PostDetailView.as_view(), name='post-detail'),
    path('posts/<slug:slug>/publish/', PostPublishView.as_view(), name='post-publish'),
    path('sitemap/', PostSitemapView.as_view(), name='post-sitemap'),
]
