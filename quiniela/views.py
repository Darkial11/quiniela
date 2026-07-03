""" quiniela / views """
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect
from django.template import TemplateDoesNotExist
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.utils import timezone

import json
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image
)

from .models import Partido, Pronostico, Jornada, Pago, Torneo
from usuarios.models import Perfil


@login_required(login_url='/login/')
def inicio(request, torneo_slug, jornada=1):

    torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()

    if not torneo_obj:
        return HttpResponse(status=404)

    jornada_obj = Jornada.objects.filter(
        torneo=torneo_obj,
        numero=jornada
    ).first()

    if not jornada_obj:
        return HttpResponse(status=404)

    partidos = Partido.objects.filter(
        jornada=jornada_obj
    ).order_by('fecha_partido')

    jornadas_ids = Partido.objects.filter(
        jornada__torneo=torneo_obj
    ).values_list('jornada', flat=True).distinct()

    jornadas = Jornada.objects.filter(
        id__in=jornadas_ids
    ).order_by('numero')

    if torneo_obj.tipo_cobro == 'unico':

        pago_confirmado_jornada = request.user.perfil.pago_confirmado

    else:

        pago_confirmado_jornada = Pago.objects.filter(
            user=request.user,
            jornada=jornada_obj,
            confirmado=True
        ).exists()

    return render(

        request,

        'quiniela/quiniela.html',

        {

            'partidos': partidos,

            'jornadas': jornadas,

            'jornada_actual': jornada_obj.numero,

            'jornada_obj': jornada_obj,

            'torneo': torneo_obj,

            'pago_confirmado_jornada': pago_confirmado_jornada,

        }

    )


@login_required(login_url='/login/')
def guardar_pronosticos(request, torneo_slug):

    if request.method == 'POST':

        torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()

        if not torneo_obj:
            return JsonResponse({'mensaje': 'Torneo no encontrado'}, status=404)

        if not torneo_obj.activo:
            return JsonResponse(
                {'mensaje': 'Este torneo ya cerró, no se aceptan más pronósticos'},
                status=403
            )

        data = json.loads(request.body)

        user = request.user

        if not user.perfil.participando:
            user.perfil.participando = True
            user.perfil.save()

        pronosticos = data['pronosticos']

        primer_partido = Partido.objects.get(
            id=pronosticos[0]['partido_id']
        )

        if primer_partido.jornada.torneo_id != torneo_obj.id:
            return JsonResponse(
                {'mensaje': 'La jornada no pertenece a este torneo'},
                status=400
            )

        Pronostico.objects.filter(
            user=user,
            partido__jornada=primer_partido.jornada
        ).delete()

        if not primer_partido.jornada.abierta:
            return JsonResponse({'mensaje': 'Jornada cerrada'})

        for item in pronosticos:

            partido = Partido.objects.get(id=item['partido_id'])

            Pronostico.objects.create(
                user=user,
                partido=partido,
                seleccion=item['seleccion']
            )

        jornada_actual = primer_partido.jornada

        if jornada_actual.torneo.tipo_cobro == 'por_jornada':

            Pago.objects.get_or_create(
                user=user,
                jornada=jornada_actual
            )

        return JsonResponse({'mensaje': 'Pronósticos guardados'})


@login_required(login_url='/login/')
def ver_pronosticos(request, torneo_slug):

    torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()

    if not torneo_obj:
        return HttpResponse(status=404)

    todas_jornadas = Jornada.objects.filter(
        torneo=torneo_obj
    ).order_by('numero')

    jornada_param = request.GET.get('jornada')

    if jornada_param:

        jornada = todas_jornadas.filter(numero=jornada_param).first()

    else:

        jornada = todas_jornadas.filter(abierta=True).order_by('numero').first()

    if not jornada:

        jornada = todas_jornadas.first()

    if not jornada:

        return render(
            request,
            'quiniela/pronosticos.html',
            {
                'torneo': torneo_obj,
                'todas_jornadas': todas_jornadas,
                'bloque': None,
            }
        )

    partidos = list(
        Partido.objects.filter(jornada=jornada).order_by('id')
    )

    if torneo_obj.tipo_cobro == 'unico':

        participantes = list(
            User.objects.filter(
                perfil__pago_confirmado=True
            ).distinct().select_related('perfil')
        )

    else:

        participantes = list(
            User.objects.filter(
                pago__jornada=jornada,
                pago__confirmado=True
            ).distinct().select_related('perfil')
        )

    pronosticos_jornada = Pronostico.objects.filter(
        partido__jornada=jornada
    ).select_related('partido', 'user')

    mapa = {}

    for p in pronosticos_jornada:
        mapa[(p.user_id, p.partido_id)] = p

    tabla = []

    for participante in participantes:

        fila_pronosticos = []
        total = 0

        for partido in partidos:

            pronostico = mapa.get((participante.id, partido.id))

            if pronostico:

                seleccion = pronostico.seleccion
                acierto = (seleccion == partido.resultado_real)

                if acierto:
                    total += 1

            else:

                seleccion = "-"
                acierto = False

            fila_pronosticos.append({
                'seleccion': seleccion,
                'acierto': acierto
            })

        nick = getattr(
            getattr(participante, 'perfil', None),
            'nick',
            participante.username
        )

        tabla.append({
            'nombre': nick,
            'pronosticos': fila_pronosticos,
            'total': total
        })

    tabla = sorted(tabla, key=lambda x: x['total'], reverse=True)

    bloque = {
        'jornada': jornada,
        'partidos': partidos,
        'tabla': tabla
    }

    return render(
        request,
        'quiniela/pronosticos.html',
        {
            'bloque': bloque,
            'todas_jornadas': todas_jornadas,
            'torneo': torneo_obj,
        }
    )

@login_required(login_url='/login/')
def cargar_pronosticos(request, torneo_slug, jornada):

    user = request.user

    pronosticos = Pronostico.objects.filter(
        user=user,
        partido__jornada__torneo__slug=torneo_slug,
        partido__jornada__numero=jornada
    )

    data = []

    for pronostico in pronosticos:
        data.append({
            'partido_id': pronostico.partido.id,
            'seleccion': pronostico.seleccion
        })

    return JsonResponse(data, safe=False)


@login_required(login_url='/login/')
def ranking(request, torneo_slug):

    torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()

    if not torneo_obj:
        return HttpResponse(status=404)

    tabla = {}

    if torneo_obj.tipo_cobro == 'unico':

        for perfil in Perfil.objects.filter(pago_confirmado=True).select_related('user'):
            tabla[perfil.nick] = 0

        pronosticos = Pronostico.objects.select_related(
            'user__perfil', 'partido'
        ).filter(
            user__perfil__pago_confirmado=True,
            partido__jornada__torneo=torneo_obj
        )

        for pronostico in pronosticos:

            nick = getattr(
                getattr(pronostico.user, 'perfil', None),
                'nick',
                pronostico.user.username
            )

            if nick not in tabla:
                tabla[nick] = 0

            if pronostico.partido.resultado_real == pronostico.seleccion:
                tabla[nick] += 1

    else:

        pagos_confirmados = Pago.objects.filter(
            jornada__torneo=torneo_obj,
            confirmado=True
        ).select_related('user__perfil')

        jornadas_pagadas = set()

        for pago in pagos_confirmados:

            nick = getattr(
                getattr(pago.user, 'perfil', None),
                'nick',
                pago.user.username
            )

            if nick not in tabla:
                tabla[nick] = 0

            jornadas_pagadas.add((pago.user_id, pago.jornada_id))

        pronosticos = Pronostico.objects.select_related(
            'user__perfil', 'partido'
        ).filter(
            partido__jornada__torneo=torneo_obj
        )

        for pronostico in pronosticos:

            clave = (pronostico.user_id, pronostico.partido.jornada_id)

            if clave not in jornadas_pagadas:
                continue

            nick = getattr(
                getattr(pronostico.user, 'perfil', None),
                'nick',
                pronostico.user.username
            )

            if pronostico.partido.resultado_real == pronostico.seleccion:
                tabla[nick] += 1

    ranking_ordenado = sorted(
        tabla.items(),
        key=lambda x: x[1],
        reverse=True
    )

    if ranking_ordenado:

        puntos_primer_lugar = ranking_ordenado[0][1]

        top3 = [
            jugador for jugador in ranking_ordenado
            if jugador[1] == puntos_primer_lugar
        ]

        resto = ranking_ordenado[len(top3):]

    else:

        top3 = []
        resto = []

    return render(
        request,
        'quiniela/ranking.html',
        {
            'top3': top3,
            'resto': resto,
            'torneo': torneo_obj,
        }
    )


def agregar_numero_pagina(canvas, doc):

    from zoneinfo import ZoneInfo

    pagina = canvas.getPageNumber()

    texto = f"Página {pagina}"

    canvas.setFont("Helvetica", 9)

    canvas.drawRightString(760, 15, texto)

    hora_mexico = timezone.now().astimezone(ZoneInfo("America/Mexico_City"))

    fecha_texto = hora_mexico.strftime("Generado: %d/%m/%Y %H:%M hrs")

    canvas.drawString(20, 15, fecha_texto)


@login_required(login_url='/login/')
def exportar_pdf_jornada(request, torneo_slug, jornada):

    torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()

    if not torneo_obj:
        return HttpResponse(status=404)

    jornada_obj = Jornada.objects.filter(
        torneo=torneo_obj,
        numero=jornada
    ).first()

    if not jornada_obj:
        return HttpResponse(status=404)

    partidos = Partido.objects.filter(jornada=jornada_obj).order_by('id')

    if torneo_obj.tipo_cobro == 'unico':

        participantes = sorted(
            User.objects.filter(perfil__pago_confirmado=True).distinct(),
            key=lambda u: getattr(getattr(u, 'perfil', None), 'nick', u.username).lower()
        )

    else:

        participantes = sorted(
            User.objects.filter(
                pago__jornada=jornada_obj,
                pago__confirmado=True
            ).distinct(),
            key=lambda u: getattr(getattr(u, 'perfil', None), 'nick', u.username).lower()
        )

    response = HttpResponse(content_type='application/pdf')

    response['Content-Disposition'] = (
        f'attachment; filename="jornada_{jornada}.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(letter),
        rightMargin=20,
        leftMargin=20,
        topMargin=20,
        bottomMargin=20
    )

    elementos = []
    estilos = getSampleStyleSheet()

    ruta_logo = os.path.join(
        settings.BASE_DIR, 'static', 'img', 'logo_fut_black.png'
    )

    logo = Image(ruta_logo, width=170, height=40)
    elementos.append(logo)

    titulo = Paragraph(
        f"<b>{torneo_obj.nombre} - Jornada {jornada}</b>",
        estilos['Title']
    )

    elementos.append(titulo)
    elementos.append(Spacer(1, 20))

    bloques_partidos = [
        partidos[i:i + 8]
        for i in range(0, len(partidos), 8)
    ]

    for indice_bloque, bloque in enumerate(bloques_partidos):

        encabezados = ["#", "Participante"]

        for partido in bloque:
            encabezados.append(f"{partido.local}\nvs\n{partido.visitante}")

        encabezados.append("Total")

        data = [encabezados]
        posicion = 1

        for participante in participantes:

            fila = []
            total = 0

            fila.append(str(posicion))

            nick = getattr(
                getattr(participante, 'perfil', None),
                'nick',
                participante.username
            )

            fila.append(nick)

            for partido in bloque:

                pronostico = Pronostico.objects.filter(
                    user=participante,
                    partido=partido
                ).first()

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

        anchos_columnas = [35, 110]

        for _ in bloque:
            anchos_columnas.append(65)

        anchos_columnas.append(45)

        tabla = Table(data, colWidths=anchos_columnas)

        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#111827")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.gray),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F3F4F6")),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ]))

        subtitulo = Paragraph(
            f"<b>Partidos {indice_bloque * 8 + 1} - {indice_bloque * 8 + len(bloque)}</b>",
            estilos['Heading2']
        )

        elementos.append(subtitulo)
        elementos.append(Spacer(1, 12))
        elementos.append(tabla)
        elementos.append(Spacer(1, 30))

    doc.build(
        elementos,
        onFirstPage=agregar_numero_pagina,
        onLaterPages=agregar_numero_pagina
    )

    return response


def reglamento_torneo(request, torneo_slug):

    torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()

    if not torneo_obj:
        return HttpResponse(status=404)

    template_name = f'quiniela/reglamento_{torneo_obj.slug}.html'

    try:

        return render(
            request,
            template_name,
            {'torneo': torneo_obj}
        )

    except TemplateDoesNotExist:

        return render(
            request,
            'quiniela/reglamento_generico.html',
            {'torneo': torneo_obj}
        )


@user_passes_test(lambda u: u.is_staff, login_url='/login/')
def admin_cargar_pronostico(request):

    jornadas = Jornada.objects.select_related('torneo').order_by(
        'torneo__nombre', 'numero'
    )

    usuarios = User.objects.select_related('perfil').order_by('perfil__nick')

    jornada_id = request.GET.get('jornada_id') or request.POST.get('jornada_id')
    user_id = request.GET.get('user_id') or request.POST.get('user_id')

    jornada_obj = None
    usuario_obj = None
    partidos = []
    pronosticos_existentes = {}
    ya_existian = False
    pago_obj = None

    if jornada_id:
        jornada_obj = Jornada.objects.select_related('torneo').filter(
            id=jornada_id
        ).first()

    if user_id:
        usuario_obj = User.objects.select_related('perfil').filter(
            id=user_id
        ).first()

    if jornada_obj:
        partidos = Partido.objects.filter(jornada=jornada_obj).order_by('id')

    if jornada_obj and usuario_obj:

        existentes = Pronostico.objects.filter(
            user=usuario_obj,
            partido__jornada=jornada_obj
        )

        pronosticos_existentes = {
            p.partido_id: p.seleccion for p in existentes
        }

        ya_existian = existentes.exists()

        if jornada_obj.torneo.tipo_cobro == 'por_jornada':

            pago_obj = Pago.objects.filter(
                user=usuario_obj,
                jornada=jornada_obj
            ).first()

    if request.method == 'POST' and jornada_obj and usuario_obj:

        confirmar_sobrescritura = request.POST.get('confirmar_sobrescritura') == '1'

        if ya_existian and not confirmar_sobrescritura:

            messages.warning(
                request,
                f'{usuario_obj.perfil.nick} ya tiene pronósticos guardados '
                f'en esta jornada. Revisa los valores precargados abajo y '
                f'dale "Guardar y sobrescribir" si quieres reemplazarlos.'
            )

        else:

            Pronostico.objects.filter(
                user=usuario_obj,
                partido__jornada=jornada_obj
            ).delete()

            guardados = 0

            for partido in partidos:

                seleccion = request.POST.get(f'partido_{partido.id}')

                if seleccion in ('L', 'E', 'V'):

                    Pronostico.objects.create(
                        user=usuario_obj,
                        partido=partido,
                        seleccion=seleccion
                    )

                    guardados += 1

            if not usuario_obj.perfil.participando:
                usuario_obj.perfil.participando = True
                usuario_obj.perfil.save()

            if jornada_obj.torneo.tipo_cobro == 'por_jornada':

                pago_obj, _ = Pago.objects.get_or_create(
                    user=usuario_obj,
                    jornada=jornada_obj
                )

                if request.POST.get('confirmar_pago') == '1':

                    pago_obj.confirmado = True
                    pago_obj.fecha_confirmacion = timezone.now()
                    pago_obj.confirmado_por = request.user
                    pago_obj.save()

            messages.success(
                request,
                f'{guardados} pronósticos guardados para {usuario_obj.perfil.nick} '
                f'— Jornada {jornada_obj.numero} ({jornada_obj.torneo.nombre}).'
            )

            existentes = Pronostico.objects.filter(
                user=usuario_obj,
                partido__jornada=jornada_obj
            )

            pronosticos_existentes = {
                p.partido_id: p.seleccion for p in existentes
            }

            ya_existian = True

    return render(
        request,
        'quiniela/admin_cargar_pronostico.html',
        {
            'jornadas': jornadas,
            'usuarios': usuarios,
            'jornada_obj': jornada_obj,
            'usuario_obj': usuario_obj,
            'partidos': partidos,
            'pronosticos_existentes': pronosticos_existentes,
            'ya_existian': ya_existian,
            'pago_obj': pago_obj,
        }
    )
