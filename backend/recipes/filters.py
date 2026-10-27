import django_filters
from django.db.models import Exists, OuterRef

from .models import Favorite, Recipe, ShoppingCart


class RecipeFilter(django_filters.FilterSet):
    tags = django_filters.CharFilter(method='filter_tags')
    is_favorited = django_filters.NumberFilter(
        method='filter_is_favorited',
    )
    is_in_shopping_cart = django_filters.NumberFilter(
        method='filter_is_in_shopping_cart',
    )

    class Meta:
        model = Recipe
        fields = ('author',)

    def filter_tags(self, queryset, name, value):
        tags = self.request.query_params.getlist('tags')
        if tags:
            return queryset.filter(tags__slug__in=tags).distinct()
        return queryset

    def filter_is_favorited(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        favorites = Favorite.objects.filter(
            user=user,
            recipe=OuterRef('pk'),
        )
        queryset = queryset.annotate(
            user_favorited=Exists(favorites),
        )
        if value == 1:
            return queryset.filter(user_favorited=True)
        if value == 0:
            return queryset.filter(user_favorited=False)
        return queryset

    def filter_is_in_shopping_cart(self, queryset, name, value):
        user = self.request.user
        if not user.is_authenticated:
            return queryset.none() if value == 1 else queryset

        shopping_cart = ShoppingCart.objects.filter(
            user=user,
            recipe=OuterRef('pk'),
        )
        queryset = queryset.annotate(
            user_in_shopping_cart=Exists(shopping_cart),
        )
        if value == 1:
            return queryset.filter(user_in_shopping_cart=True)
        if value == 0:
            return queryset.filter(user_in_shopping_cart=False)
        return queryset