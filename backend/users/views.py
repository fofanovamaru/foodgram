from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Follow, User
from .serializers import (
    AvatarSerializer,
    CustomUserSerializer,
)
from .subscription_serializers import (
    SubscribeSerializer,
    SubscriptionSerializer,
)


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        users = User.objects.filter(
            followers__user=request.user,
        ).order_by('id')

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
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, id=None):
        target_user = get_object_or_404(User, id=id)

        serializer = SubscribeSerializer(
            data={'following': target_user.id},
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)

        response_serializer = SubscriptionSerializer(
            target_user,
            context=self.get_serializer_context(),
        )
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        target_user = get_object_or_404(User, id=id)

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
        methods=('put',),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request):
        serializer = AvatarSerializer(
            request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @avatar.mapping.delete
    def delete_avatar(self, request):
        request.user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)