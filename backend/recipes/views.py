from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
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
from .serializers import (
    IngredientSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    TagSerializer,
)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = (AllowAny,)
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (AllowAny,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related(
        'author',
    ).prefetch_related(
        'tags',
        'recipe_ingredients__ingredient',
    )
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return RecipeWriteSerializer
        return RecipeReadSerializer

    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied(
                'Изменять можно только свои рецепты.'
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(
                'Удалять можно только свои рецепты.'
            )
        instance.delete()

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
            RecipeReadSerializer(
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
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def favorite(self, request, pk=None):
        if request.method == 'POST':
            return self._change_user_recipe_relation(
                request, Favorite
            )
        return self._remove_user_recipe_relation(
            request, Favorite
        )

    @action(
        detail=True,
        methods=('post', 'delete'),
        permission_classes=(IsAuthenticated,),
    )
    def shopping_cart(self, request, pk=None):
        if request.method == 'POST':
            return self._change_user_recipe_relation(
                request, ShoppingCart
            )
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

        lines = ['Список покупок', '']

        for item in ingredients:
            lines.append(
                f"{item['ingredient__name']} "
                f"({item['ingredient__measurement_unit']}) — "
                f"{item['total_amount']}"
            )

        response = HttpResponse(
            '\n'.join(lines),
            content_type='text/plain; charset=utf-8',
        )
        response['Content-Disposition'] = (
            'attachment; filename="shopping_list.txt"'
        )
        return response


def redirect_to_recipe(request, recipe_id):
    get_object_or_404(Recipe, id=recipe_id)
    return redirect(f'/recipes/{recipe_id}/')
