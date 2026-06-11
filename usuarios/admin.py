from django.contrib import admin
from django.contrib import messages
from .models import Perfil
from quiniela.models import Pronostico, Jornada
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
                "subject": "⏳ Hoy Inicia el Mundial — Confirma tu lugar en la Quiniela",
                "text": (
                    f"Hola {perfil.nick},\n\n"
                    "El Mundial 2026 arranca Hoy 11 de junio y aún no has confirmado tu participación.\n\n"
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

def enviar_pdfs_cierre(modeladmin, request, queryset):
    import io
    import os
    import base64
    from django.conf import settings
    from django.contrib.auth.models import User
    from quiniela.models import Jornada, Partido, Pronostico
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from zoneinfo import ZoneInfo
    from django.utils import timezone

    def generar_pdf_jornada(jornada_obj):

        partidos = list(Partido.objects.filter(jornada=jornada_obj).order_by('id'))

        participantes = sorted(
            User.objects.filter(perfil__pago_confirmado=True).distinct(),
            key=lambda u: getattr(getattr(u, 'perfil', None), 'nick', u.username).lower()
        )

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            rightMargin=20, leftMargin=20,
            topMargin=20, bottomMargin=20
        )

        elementos = []
        estilos = getSampleStyleSheet()

        ruta_logo = os.path.join(settings.BASE_DIR, 'static', 'img', 'logo_fut_black.png')
        logo = Image(ruta_logo, width=170, height=40)
        elementos.append(logo)

        titulo = Paragraph(f"<b>Quiniela Mundial 2026 - Jornada {jornada_obj.numero}</b>", estilos['Title'])
        elementos.append(titulo)
        elementos.append(Spacer(1, 20))

        bloques_partidos = [partidos[i:i+8] for i in range(0, len(partidos), 8)]

        for indice_bloque, bloque in enumerate(bloques_partidos):

            encabezados = ["#", "Participante"]
            for partido in bloque:
                encabezados.append(f"{partido.local}\nvs\n{partido.visitante}")
            encabezados.append("Total")

            data = [encabezados]
            posicion = 1

            for participante in participantes:
                fila = [str(posicion), getattr(getattr(participante, 'perfil', None), 'nick', participante.username)]
                total = 0
                for partido in bloque:
                    pronostico = Pronostico.objects.filter(user=participante, partido=partido).first()
                    if pronostico:
                        seleccion = pronostico.seleccion
                        if partido.resultado_real == seleccion:
                            total += 1
                    else:
                        seleccion = "-"
                    fila.append(seleccion)
                fila.append(str(total))
                data.append(fila)
                posicion += 1

            anchos_columnas = [35, 110] + [65] * len(bloque) + [45]

            tabla = Table(data, colWidths=anchos_columnas)
            tabla.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#111827")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 1, colors.gray),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F3F4F6")),
                ('TEXTCOLOR', (0,1), (-1,-1), colors.black),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ]))

            subtitulo = Paragraph(f"<b>Partidos {indice_bloque*8+1} - {indice_bloque*8+len(bloque)}</b>", estilos['Heading2'])
            elementos.append(subtitulo)
            elementos.append(Spacer(1, 12))
            elementos.append(tabla)
            elementos.append(Spacer(1, 30))

        doc.build(elementos)
        buffer.seek(0)
        return buffer.read()

    resend.api_key = settings.RESEND_API_KEY

    jornadas = Jornada.objects.all().order_by('numero')
    adjuntos = []

    for jornada in jornadas:
        pdf_bytes = generar_pdf_jornada(jornada)
        adjuntos.append({
            "filename": f"Jornada_{jornada.numero}.pdf",
            "content": list(pdf_bytes),
            "type": "application/pdf",
        })

    pagados = Perfil.objects.filter(pago_confirmado=True)
    enviados = 0

    for perfil in pagados:
        if not perfil.user.email:
            continue
        try:
            resend.Emails.send({
                "from": "Quiniela LukiFix <contacto@lukifix.mx>",
                "to": [perfil.user.email],
                "subject": "🏆 Quiniela Mundial 2026 — PDFs de todas las Jornadas",
                "text": (
                    f"Hola {perfil.nick},\n\n"
                    "¡El Mundial 2026 ha comenzado! Adjunto encontrarás los PDFs con todos los pronósticos de las jornadas.\n\n"
                    "¡Mucha suerte y que gane el mejor!\n\n"
                    "— Equipo LukiFix"
                ),
                "attachments": adjuntos,
            })
            enviados += 1
        except Exception:
            pass

    modeladmin.message_user(request, f"PDFs enviados correctamente a {enviados} participantes.", messages.SUCCESS)

enviar_pdfs_cierre.short_description = "📎 Enviar PDFs de todas las jornadas a participantes"

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
                        f"Ya pagaste tu participación pero aún tienes pronósticos sin llenar en las Jornadas {jornada.numero}.\n\n"
                        f"Llevas {pronosticos} de {total_partidos} partidos seleccionados.\n\n"
                        "Entra ahora y completa tu quiniela antes del 11 de junio 2026 a las 12:30pm.\n"
                        "Ultima Oportunidad.\n"
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

    def sin_pronosticos(self, obj):
        if not obj.pago_confirmado:
            return '-'
        total = Pronostico.objects.filter(user=obj.user).count()
        if total == 0:
            return '⚠️ Sin pronósticos'
        jornadas = Jornada.objects.all().count()
        return f'{total} pronósticos'

    sin_pronosticos.short_description = 'Pronósticos'

    list_display = (
        'user',
        'nick',
        'telefono',
        'participando',
        'pago_confirmado',
        'fecha_pago',
        'tipo_pago',
        'sin_pronosticos'
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
        enviar_recordatorio_quiniela,
        enviar_pdfs_cierre
    ]
