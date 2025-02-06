from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.serializers import SubscribeSerializer
from user.models import Users, Follow
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

    def list(self, request, *args, **kwargs):
        user_id = self.request.user.id
        instance = self.get_queryset().get(id=user_id)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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
    def post_subscribe(self, request, **kwargs):
        following = get_object_or_404(Users, pk=self.kwargs.get('id'))
        serializer = SubscribeSerializer(
            data={
                'user': request.user.id,
                'subscribing': following.id,
            },
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @post_subscribe.mapping.delete
    def delete_subscribe(self, request, *args, **kwargs):
        following = get_object_or_404(Users, pk=self.kwargs.get('id'))
        follow = Follow.get_object_or_404(
            user=request.user, subscribing=following)
        if follow:
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(
            {'error': 'Вы не подписаны на этого пользователя.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(
        methods=['get'], detail=False, 
        url_path='subscriptions',
        permission_classes=[permissions.IsAuthenticated]
    )
    def get_subscriptions(self, request):
        user_subscriptions = Follow.get_object_or_404(
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
    def put_avatar(self, request):
        user = request.user

        serializer = UserAvatarSerializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @put_avatar.mapping.delete
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
