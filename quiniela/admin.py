""" quiniela / admin """
from django.contrib import admin

from .models import (
    Partido,
    Pronostico,
    Jornada
)

admin.site.register(Partido)
admin.site.register(Pronostico)
admin.site.register(Jornada)
