from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from user.models import Follow, Users
from api.serializers import SubscribeSerializer
from user.paginations import Pagination
from user.serializers import (
    UserAvatarSerializer,
    UserSerializer,
)


class UsersViewSet(UserViewSet):
    queryset = Users.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = Pagination

    @action(
        methods=['get'], detail=False,
        url_path='me', permission_classes=[permissions.IsAuthenticated]
    )
    def get_me(self, request):
        user_me = get_object_or_404(Users, id=request.user.id)
        serializer = UserSerializer(user_me)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['post'], detail=True,
        url_path='subscribe',
        permission_classes=[permissions.IsAuthenticated]
    )
    def post_subscribe(self, request, id):
        user = request.user
        data = {'user': user.id, 'author': id}
        serializer = SubscribeSerializer(
            data=data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=HTTP_201_CREATED)

    @post_subscribe.mapping.delete
    def delete_subscribe(self, request, id):
        user = request.user
        author = get_object_or_404(Users, id=id)
        follow = Follow.objects.filter(user=user, author=author)
        if follow.exists():
            follow.delete()
            return Response(status=HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Вы не подписаны на этого автора'},
            status=HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['get'], detail=False, 
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_subscriptions(self, request):
        user_subscriptions = Follow.objects.filter(
            user=self.request.user
        )
        paginator = self.paginate_queryset(user_subscriptions)
        serializer = SubscribeSerializer(
            paginator,
            context={'request': request},
            many=True
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=False, methods=['put'],
        url_path='me/avatar',
        permission_classes=[permissions.IsAuthenticated]
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
            user.avatar.delete(save=False)
            user.avatar = None
            user.save()
            return Response(
                {'status': 'Аватар удален.'},
                status=status.HTTP_204_NO_CONTENT
            )
        return Response(
            {'errors': 'Такого объекта не существует.'},
            status=status.HTTP_404_NOT_FOUND
        )
