""" quiniela / admin """
from django.contrib import admin

from .models import (
    Partido,
    Pronostico,
    Jornada
)


@admin.register(Pronostico)
class PronosticoAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'get_jornada',
        'partido',
        'seleccion',
    )

    list_filter = (
        'partido__jornada',
    )

    search_fields = (
        'user__username',
    )

    def get_jornada(self, obj):
        return obj.partido.jornada

    get_jornada.short_description = 'Jornada'


admin.site.register(Partido)
admin.site.register(Jornada)