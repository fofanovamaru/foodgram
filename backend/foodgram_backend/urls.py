from django.contrib import admin
from django.urls import include, path

from recipes.views import redirect_to_recipe

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('s/<int:recipe_id>/', redirect_to_recipe, name='short-link'),
    path('api/', include('recipes.urls')),
    path('api/', include('users.urls')),
]
