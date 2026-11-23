
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from .models import User


class CustomUserCreateSerializer(UserCreateSerializer):
    first_name = serializers.CharField(
        required=True,
        allow_blank=False,
    )
    last_name = serializers.CharField(
        required=True,
        allow_blank=False,
    )

    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        from .models import Follow

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False

        return Follow.objects.filter(
            user=request.user,
            following=obj,
        ).exists()


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
