from rest_framework import serializers

from recipes.models import Recipe

from .models import Follow
from .serializers import CustomUserSerializer


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follow
        fields = ('following',)

    def validate_following(self, following):
        user = self.context['request'].user

        if following == user:
            raise serializers.ValidationError(
                'Нельзя подписаться на себя.'
            )

        if Follow.objects.filter(
            user=user,
            following=following,
        ).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на этого пользователя.'
            )

        return following


class SubscriptionRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


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
        limit = (
            request.query_params.get('recipes_limit')
            if request else None
        )

        recipes = Recipe.objects.filter(
            author=obj,
        ).order_by('-pub_date')

        if limit and limit.isdigit():
            recipes = recipes[:int(limit)]

        return SubscriptionRecipeSerializer(
            recipes,
            many=True,
            context=self.context,
        ).data