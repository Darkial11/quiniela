""" usuarios /urls """
from django.urls import path

from . import views

urlpatterns = [
    path(
        'dashboard/',
        views.dashboard,
        name='dashboard'
    ),
    path(
        '',
        views.home,
        name='home'
    ),

    path(
        'registro/',
        views.registro,
        name='registro'
    ),

    path(
        'login/',
        views.iniciar_sesion,
        name='login'
    ),

    path(
        'logout/',
        views.cerrar_sesion,
        name='logout'
    ),

    path(
        'reglamento/',
        views.reglamento
    ),
]
