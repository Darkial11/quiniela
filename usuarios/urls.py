""" usuarios /urls """
from django.urls import path

from . import views

urlpatterns = [
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
        'recuperar-contrasena/',
        views.recuperar_contrasena,
        name='recuperar_contrasena'
    ),

    path(
        'recuperar-contrasena/confirmar/<uidb64>/<token>/',
        views.confirmar_contrasena,
        name='confirmar_contrasena'
    ),

    path(

    "contacto/",

    views.contacto,

    name="contacto"

    ),
]
