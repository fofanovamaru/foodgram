import base64
import binascii
import uuid

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers

from recipes.models import Recipe
from recipes.serializers import RecipeReadSerializer

from .models import Follow, User


class CustomUserCreateSerializer(UserCreateSerializer):
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
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(
            user=request.user,
            following=obj,
        ).exists()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data['first_name'] and not data['last_name']:
            data['first_name'] = instance.username
        return data


class SubscriptionSerializer(CustomUserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True,
    )

    class Meta(CustomUserSerializer.Meta):
        fields = CustomUserSerializer.Meta.fields + (
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.query_params.get('recipes_limit') if request else None

        recipes = Recipe.objects.filter(author=obj).order_by('-pub_date')
        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]

        return RecipeReadSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image/'):
            try:
                header, encoded = data.split(',', 1)
                image_type = header.split(';')[0].split('/')[-1].lower()

                extensions = {
                    'jpeg': 'jpg',
                    'jpg': 'jpg',
                    'png': 'png',
                }
                extension = extensions.get(image_type)

                if not extension:
                    raise serializers.ValidationError(
                        'Поддерживаются только JPG и PNG.'
                    )

                decoded = base64.b64decode(encoded, validate=True)

                data = ContentFile(
                    decoded,
                    name=f'avatar_{uuid.uuid4().hex}.{extension}',
                )
            except (ValueError, binascii.Error):
                raise serializers.ValidationError(
                    'Некорректный формат изображения.'
                )

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
