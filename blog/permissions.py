from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Anyone may read. Only the post's author may change it."""
    message = 'You can only edit your own posts.'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author_id == request.user.id
