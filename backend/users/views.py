from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .models import Follow, User
from .serializers import (
    AvatarSerializer,
    CustomUserSerializer,
    SubscriptionSerializer,
)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    def get_permissions(self):
        if self.action in (
            'me',
            'avatar',
            'subscriptions',
            'subscribe',
        ):
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        users = User.objects.filter(
            followers__user=request.user,
        ).distinct().order_by('id')

        page = self.paginate_queryset(users)
        serializer = SubscriptionSerializer(
            page if page is not None else users,
            many=True,
            context=self.get_serializer_context(),
        )

        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        target_user = get_object_or_404(User, id=id)

        if request.method == 'POST':
            if target_user == request.user:
                raise ValidationError(
                    {'errors': 'Нельзя подписаться на себя.'}
                )

            _, created = Follow.objects.get_or_create(
                user=request.user,
                following=target_user,
            )

            if not created:
                raise ValidationError(
                    {'errors': 'Вы уже подписаны на этого пользователя.'}
                )

            serializer = SubscriptionSerializer(
                target_user,
                context=self.get_serializer_context(),
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

        deleted, _ = Follow.objects.filter(
            user=request.user,
            following=target_user,
        ).delete()

        if not deleted:
            raise ValidationError(
                {'errors': 'Вы не подписаны на этого пользователя.'}
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                request.user,
                data=request.data,
                partial=True,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)

        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)