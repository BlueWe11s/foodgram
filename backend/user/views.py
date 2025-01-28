from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.views import TokenObtainPairView

from recipes.permissions import (IsAdminOnly)
from user.serializers import (AuthSerializer,
                              TokenSerializer,
                              UserSerializer)

User = get_user_model()


class UserSignupView(APIView):
    '''
    Регистрация нового пользователя
    '''
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = AuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.get(
            username=request.data.get('username'),
            email=request.data.get('email')
        )
        confirmation_code = default_token_generator.make_token(user)
        send_mail(
            'Код подтверждения',
            f'Ваш код - {confirmation_code}',
            settings.SENDER_EMAIL,
            [request.data.get('email')]
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class ObtainTokenView(TokenObtainPairView):
    '''
    Получение токена
    '''
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = TokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User, username=request.data.get('username')
        )
        if not default_token_generator.check_token(
                user, request.data.get('confirmation_code')
        ):
            return Response(
                'Неверный confirmation_code',
                status=status.HTTP_400_BAD_REQUEST
            )
        token = {'token': str(AccessToken.for_user(user))}
        return Response(token, status=status.HTTP_200_OK)


class UserViewSet(viewsets.ModelViewSet):
    '''
    Работа с пользователями
    '''
    serializer_class = UserSerializer
    queryset = User.objects.order_by('pk')
    permission_classes = (IsAdminOnly,)
    lookup_field = 'username'
    filter_backends = (filters.SearchFilter,)
    search_fields = ('=username',)
    pagination_class = PageNumberPagination
    http_method_names = ['get', 'delete', 'post', 'patch']

    @action(
        methods=['GET'], detail=False, url_path='me',
        permission_classes=(permissions.IsAuthenticated,)
    )
    def get_update_me(self, request):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )

    @get_update_me.mapping.patch
    def patch_me(self, request):
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True
        )
        if serializer.is_valid(raise_exception=True):
            serializer.validated_data.pop('role', None)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST
        )
