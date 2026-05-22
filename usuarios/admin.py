from django.contrib import admin

from .models import Perfil


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):

    list_display = (

        'user',

        'nick',

        'telefono',

        'participando',

        'pago_confirmado',

        'fecha_pago',

        'tipo_pago'

    )

    list_filter = (

        'participando',

        'pago_confirmado',

        'tipo_pago'

    )

    search_fields = (

        'user__username',

        'nick',

        'telefono'

    )