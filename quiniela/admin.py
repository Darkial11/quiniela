""" quiniela / admin """
from django.contrib import admin
from django.contrib import messages
from django.utils import timezone

from .models import (
    Partido,
    Pronostico,
    Jornada,
    Torneo,
    Pago
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

def confirmar_pago(modeladmin, request, queryset):

    actualizados = queryset.filter(confirmado=False).update(
        confirmado=True,
        fecha_confirmacion=timezone.now(),
        confirmado_por=request.user
    )

    modeladmin.message_user(
        request,
        f"{actualizados} pago(s) confirmado(s).",
        messages.SUCCESS
    )

confirmar_pago.short_description = "✅ Confirmar pago"


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):

    list_display = (
        'user',
        'jornada',
        'monto',
        'metodo',
        'confirmado',
        'fecha_confirmacion',
    )

    list_filter = (
        'jornada',
        'confirmado',
        'metodo',
    )

    search_fields = (
        'user__username',
    )

    actions = [confirmar_pago]


@admin.register(Torneo)
class TorneoAdmin(admin.ModelAdmin):

    list_display = (
        'nombre',
        'slug',
        'tipo_cobro',
        'activo',
    )

    list_filter = (
        'tipo_cobro',
        'activo',
    )


@admin.register(Partido)
class PartidoAdmin(admin.ModelAdmin):

    list_display = (
        'local',
        'visitante',
        'jornada',
        'fecha_partido',
        'hora_partido',
        'resultado_real',
    )

    list_filter = (
        'jornada__torneo',
        'jornada',
    )

    search_fields = (
        'local',
        'visitante',
    )


admin.site.register(Jornada)
