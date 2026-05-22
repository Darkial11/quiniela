""" quiniela / urls """
from django.urls import path
from . import views

urlpatterns = [
    path('quiniela/', views.inicio, name='inicio'),
    path('guardar/', views.guardar_pronosticos),
    path('pronosticos/', views.ver_pronosticos),
    path('exportar-pdf/<int:jornada>/', views.exportar_pdf_jornada),
    path('cargar/<int:jornada>/', views.cargar_pronosticos, name='cargar_pronosticos'),
    path('ranking/', views.ranking),
    path('jornada/<int:jornada>/', views.inicio),
    path('pagar/', views.crear_pago),
    path('pago-exitoso/', views.pago_exitoso),
    path('pago-error/', views.pago_error),
    path('pago-pendiente/', views.pago_pendiente),
    path('webhook/mercadopago/', views.webhook_mercadopago),
]
