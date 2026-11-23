from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response

from .filters import RecipeFilter
from .models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
)
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeShortSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)
from .utils import create_shopping_cart_file


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author',
    ).prefetch_related(
        'tags',
        'recipe_ingredients__ingredient',
    )
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsAuthorOrReadOnly,
    )
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def _change_user_recipe_relation(self, request, model):
        recipe = self.get_object()

        _, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe,
        )

        if not created:
            raise ValidationError(
                {'errors': 'Рецепт уже добавлен.'}
            )

        return Response(
            RecipeShortSerializer(
                recipe,
                context=self.get_serializer_context(),
            ).data,
            status=status.HTTP_201_CREATED,
        )

    def _remove_user_recipe_relation(self, request, model):
        recipe = self.get_object()

        deleted, _ = model.objects.filter(
            user=request.user,
            recipe=recipe,
        ).delete()

        if not deleted:
            raise ValidationError(
                {'errors': 'Рецепта нет в списке.'}
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        return self._change_user_recipe_relation(
            request, Favorite
        )

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        return self._remove_user_recipe_relation(
            request, Favorite
        )

    @action(
        detail=True,
        methods=('post',),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        return self._change_user_recipe_relation(
            request, ShoppingCart
        )

    @shopping_cart.mapping.delete
    def remove_from_shopping_cart(self, request, pk=None):
        return self._remove_user_recipe_relation(
            request, ShoppingCart
        )

    @action(
        detail=True,
        methods=('get',),
        url_path='get-link',
        permission_classes=(AllowAny,),
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        return Response({
            'short-link': request.build_absolute_uri(
                f'/s/{recipe.id}/'
            )
        })

    @action(
        detail=False,
        methods=('get',),
        permission_classes=(IsAuthenticated,),
    )
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__in_shopping_carts__user=request.user,
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit',
        ).annotate(
            total_amount=Sum('amount'),
        ).order_by('ingredient__name')

        return create_shopping_cart_file(ingredients)


def redirect_to_recipe(request, recipe_id):
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}/')
