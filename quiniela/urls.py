""" quiniela / urls """
from django.urls import path
from . import views

urlpatterns = [
    path('<slug:torneo_slug>/', views.inicio, name='inicio'),
    path('<slug:torneo_slug>/jornada/<int:jornada>/', views.inicio),
    path('<slug:torneo_slug>/guardar/', views.guardar_pronosticos),
    path('<slug:torneo_slug>/pronosticos/', views.ver_pronosticos),
    path('<slug:torneo_slug>/ranking/', views.ranking),
    path('<slug:torneo_slug>/cargar/<int:jornada>/', views.cargar_pronosticos, name='cargar_pronosticos'),
    path('<slug:torneo_slug>/exportar-pdf/<int:jornada>/', views.exportar_pdf_jornada),
    path('<slug:torneo_slug>/reglamento/', views.reglamento_torneo, name='reglamento_torneo'),
]
