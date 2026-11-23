from django.contrib import admin
from django.db.models import Count

from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name', 'measurement_unit')
    list_filter = ('name', 'measurement_unit')


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1
    validate_min = True


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'author',
        'display_tags',
        'cooking_time_display',
        'favorites_count',
    )
    list_filter = ('author', 'tags')
    search_fields = (
        'name',
        'author__username',
        'tags__name',
    )
    inlines = (RecipeIngredientInline,)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.prefetch_related(
            'tags',
        ).annotate(
            favorite_count=Count('favorited_by', distinct=True),
        )

    @admin.display(description='Теги')
    def display_tags(self, obj):
        return ', '.join(tag.name for tag in obj.tags.all())

    @admin.display(
        description='Время приготовления',
        ordering='cooking_time',
    )
    def cooking_time_display(self, obj):
        return f'{obj.cooking_time} мин.'

    @admin.display(
        description='В избранном',
        ordering='favorite_count',
    )
    def favorites_count(self, obj):
        return obj.favorite_count


admin.site.register(RecipeIngredient)
admin.site.register(Favorite)
admin.site.register(ShoppingCart)