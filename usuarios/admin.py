from django.contrib import admin
from django.contrib import messages
from .models import Perfil
import resend
from django.conf import settings


def enviar_recordatorio_pago(modeladmin, request, queryset):
    sin_pago = Perfil.objects.filter(pago_confirmado=False)
    enviados = 0
    resend.api_key = settings.RESEND_API_KEY

    for perfil in sin_pago:
        if not perfil.user.email:
            continue
        try:
            resend.Emails.send({
                "from": "Quiniela LukiFix <contacto@lukifix.mx>",
                "to": [perfil.user.email],
                "subject": "⏳ Faltan 4 días — Confirma tu lugar en la Quiniela",
                "text": (
                    f"Hola {perfil.nick},\n\n"
                    "El Mundial 2026 arranca el 11 de junio y aún no has confirmado tu participación.\n\n"
                    "Entra ahora y completa tu pago de $100 MXN para asegurar tu lugar:\n"
                    "https://quiniela.lukifix.mx/quiniela/\n\n"
                    "No te quedes fuera. ¡El que sabe, entra!\n\n"
                    "— Equipo LukiFix"
                ),
            })
            enviados += 1
        except Exception:
            pass

    modeladmin.message_user(
        request,
        f"Recordatorio de pago enviado a {enviados} usuarios.",
        messages.SUCCESS
    )

enviar_recordatorio_pago.short_description = "📩 Enviar recordatorio de PAGO a no pagados"


def enviar_recordatorio_quiniela(modeladmin, request, queryset):
    from quiniela.models import Pronostico, Jornada

    jornada = Jornada.objects.filter(abierta=True).order_by('numero').first()
    if not jornada:
        modeladmin.message_user(request, "No hay jornada abierta.", messages.WARNING)
        return

    from django.contrib.auth.models import User
    total_partidos = jornada.partido_set.count()
    pagados = Perfil.objects.filter(pago_confirmado=True)
    enviados = 0
    resend.api_key = settings.RESEND_API_KEY

    for perfil in pagados:
        pronosticos = Pronostico.objects.filter(
            user=perfil.user,
            partido__jornada=jornada
        ).count()

        if pronosticos < total_partidos:
            if not perfil.user.email:
                continue
            try:
                resend.Emails.send({
                    "from": "Quiniela LukiFix <contacto@lukifix.mx>",
                    "to": [perfil.user.email],
                    "subject": "⚽ ¡Te faltan pronósticos por llenar!",
                    "text": (
                        f"Hola {perfil.nick},\n\n"
                        f"Ya pagaste tu participación pero aún tienes pronósticos sin llenar en la Jornada {jornada.numero}.\n\n"
                        f"Llevas {pronosticos} de {total_partidos} partidos seleccionados.\n\n"
                        "Entra ahora y completa tu quiniela antes del 11 de junio:\n"
                        "https://quiniela.lukifix.mx/quiniela/\n\n"
                        "— Equipo LukiFix"
                    ),
                })
                enviados += 1
            except Exception:
                pass

    modeladmin.message_user(
        request,
        f"Recordatorio de quiniela incompleta enviado a {enviados} usuarios.",
        messages.SUCCESS
    )

enviar_recordatorio_quiniela.short_description = "⚽ Enviar recordatorio de QUINIELA incompleta"


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

    actions = [
        enviar_recordatorio_pago,
        enviar_recordatorio_quiniela
    ]