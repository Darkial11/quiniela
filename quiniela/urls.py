""" quiniela / urls """
from django.urls import path
from . import views

urlpatterns = [
    path('quiniela/', views.inicio, name='inicio'),
    path('guardar/', views.guardar_pronosticos),
    path('pronosticos/', views.ver_pronosticos),
    path('cargar/<int:jornada>/', views.cargar_pronosticos, name='cargar_pronosticos'),
    path('ranking/', views.ranking),
    path('jornada/<int:jornada>/', views.inicio),
    path('pagar/', views.crear_pago),
]
