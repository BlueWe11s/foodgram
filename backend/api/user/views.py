from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from user.models import Follow
from api.user.paginations import Pagination
from user.serializers import (
    UserAvatarSerializer,
    UserSerializer,
    SubscribeSerializer,
    SubscribingSerializer
)

User = get_user_model()


class UsersViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = Pagination

    @action(
        methods=["get"],
        detail=False,
        url_path="me",
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_me(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=["get"],
        detail=False,
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscriptions",
        url_name="subscriptions",
    )
    def get_subscribe(self, request):
        """Получить список подписок пользователя."""
        user = request.user
        subscriptions = Follow.objects.filter(user=user)
        authors = [subscription.author for subscription in subscriptions]
        pages = self.paginate_queryset(authors)
        serializer = SubscribingSerializer(
            pages, many=True, context={"request": request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        methods=["post"],
        detail=True,
        permission_classes=[permissions.IsAuthenticated],
        url_path="subscribe",
    )
    def post_subscribe(self, request, id):
        """Подписаться или отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, id=id)
        serializer = SubscribeSerializer(
            data={"user": user.id, "author": author.id},
            context={"request": request},
        )
        serializer.is_valid(raise_exception=True)
        subscription = serializer.save()
        return Response(
            SubscribeSerializer(
                subscription, context={"request": request}
            ).data,
            status=status.HTTP_201_CREATED,
        )

    @post_subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        """Подписаться или отписаться от автора."""
        user = request.user
        author = get_object_or_404(User, id=id)
        deleted_count, _ = Follow.objects.filter(
            user=user, author=author
        ).delete()
        if not deleted_count:
            return Response(
                {"errors": "Вы не подписаны на этого автора."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        url_path="favorite",
        permission_classes=[permissions.IsAuthenticated],
    )
    def favorite_post(self, request, id):
        return self.add_item_to_list(request.user, id, "favorite")

    @favorite_post.mapping.delete
    def favorite_delete(self, request, id):
        return self.remove_item_from_list(request.user, id, "favorite")

    @action(
        detail=False,
        methods=["put"],
        url_path="me/avatar",
        permission_classes=[permissions.IsAuthenticated],
    )
    def get_avatar(self, request):
        user = request.user

        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @get_avatar.mapping.delete
    def delete_avatar(self, request):
        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
            return Response(
                {"status": "Аватар удален."}, status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {"errors": "Такого объекта не существует."},
            status=status.HTTP_404_NOT_FOUND,
        )