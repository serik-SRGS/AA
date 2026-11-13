from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('api/buscar/', views.buscar_alternativas, name='buscar_alternativas'),
    path('api/menu-diario/', views.menu_diario, name='menu_diario'),
]
