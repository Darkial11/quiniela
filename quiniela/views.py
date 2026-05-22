from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect

from django.http import JsonResponse, HttpResponse

from .models import (

    Partido,

    Pronostico,

    Jornada

)

import json
import mercadopago
import os
from django.utils import timezone
from usuarios.models import Perfil

@login_required(login_url='/login/')
def inicio(request, jornada=1):

    jornada_obj = Jornada.objects.get(

        numero=jornada

    )

#---------------------------------------------
    partidos = Partido.objects.filter(

        jornada=jornada_obj

    ).order_by('fecha_partido')
#----------------------------------------------

    jornadas_ids = Partido.objects.values_list(

        'jornada',

        flat=True

    ).distinct()

    jornadas = Jornada.objects.filter(

        id__in=jornadas_ids

    ).order_by('numero')

    return render(

        request,

        'quiniela/quiniela.html',

        {

            'partidos': partidos,

            'jornadas': jornadas,

            'jornada_actual': jornada_obj.numero,

            'jornada_obj': jornada_obj,

        }

    )


@login_required(login_url='/login/')
def guardar_pronosticos(request):

    if request.method == 'POST':

        data = json.loads(request.body)

        user = request.user

        if not user.perfil.pago_confirmado:

            return JsonResponse({
            'mensaje': 'Debes pagar para participar',
            'pago_requerido': True
            })

        pronosticos = data['pronosticos']

        primer_partido = Partido.objects.get(

            id=pronosticos[0]['partido_id']

        )

        Pronostico.objects.filter(

            user=user,

            partido__jornada=primer_partido.jornada

        ).delete()

        if not primer_partido.jornada.abierta:

            return JsonResponse({

                'mensaje': 'Jornada cerrada'

            })

        for item in pronosticos:

            partido = Partido.objects.get(

                id=item['partido_id']

            )

            Pronostico.objects.create(

                user=user,

                partido=partido,

                seleccion=item['seleccion']

            )

        return JsonResponse({

            'mensaje': 'Pronósticos guardados'

        })


@login_required(login_url='/login/')
def ver_pronosticos(request):

    jornadas = Jornada.objects.all().order_by(

        'numero'

    )

    tabla_jornadas = []

    for jornada in jornadas:

        partidos = Partido.objects.filter(

            jornada=jornada

        ).order_by('id')

        participantes = User.objects.filter(

            pronostico__isnull=False

        ).distinct()

        tabla = []

        for participante in participantes:

            fila_pronosticos = []

            total = 0

            for partido in partidos:

                pronostico = Pronostico.objects.filter(

                    user=participante,

                    partido=partido

                ).first()

                if pronostico:

                    seleccion = pronostico.seleccion

                    acierto = (

                        seleccion

                        ==

                        partido.resultado_real

                    )

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

        tabla = sorted(

            tabla,

            key=lambda x: x['total'],

            reverse=True

        )

        tabla_jornadas.append({

            'jornada': jornada,

            'partidos': partidos,

            'tabla': tabla

        })

    return render(

        request,

        'quiniela/pronosticos.html',

        {

            'tabla_jornadas': tabla_jornadas

        }

    )


@login_required(login_url='/login/')
def cargar_pronosticos(request, jornada):

    user = request.user

    pronosticos = Pronostico.objects.filter(

        user=user,

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
def ranking(request):

    pronosticos = Pronostico.objects.all()

    tabla = {}

    for pronostico in pronosticos:

        nick = getattr(

            getattr(pronostico.user, 'perfil', None),

            'nick',

            pronostico.user.username

        )

        if nick not in tabla:

            tabla[nick] = 0

        if (

            pronostico.partido.resultado_real

            ==

            pronostico.seleccion

        ):

            tabla[nick] += 1

    ranking_ordenado = sorted(

        tabla.items(),

        key=lambda x: x[1],

        reverse=True

    )

    top3 = ranking_ordenado[:3]

    resto = ranking_ordenado

    return render(

        request,

        'quiniela/ranking.html',

        {

            'top3': top3,

            'resto': resto

        }

    )

@login_required(login_url='/login/')
def crear_pago(request):

    if request.user.perfil.pago_confirmado:

        return redirect('/quiniela/')

    sdk = mercadopago.SDK(

        os.environ.get("MP_ACCESS_TOKEN")

    )

    preference_data = {

        "items": [

            {

                "title": "Participacion Quiniela Mundial 2026",

                "quantity": 1,

                "currency_id": "MXN",

                "unit_price": 100

            }

        ],

        "back_urls": {

            "success":
                "https://quiniela.lukifix.mx/pago-exitoso/",

            "failure":
                "https://quiniela.lukifix.mx/pago-error/",

            "pending":
                "https://quiniela.lukifix.mx/pago-pendiente/"

        },

        "auto_return": "approved",
        
        "external_reference": str(request.user.id),

        "notification_url":
        "https://quiniela.lukifix.mx/webhook/mercadopago/",

    }

    preference_response = sdk.preference().create(

        preference_data

    )

    preference = preference_response["response"]

    return redirect(

        preference["init_point"]

    )

@login_required(login_url='/login/')
def pago_exitoso(request):

    payment_id = request.GET.get("payment_id")

    status = request.GET.get("status")

    if not payment_id:

        return redirect('/quiniela/')

    sdk = mercadopago.SDK(

        os.environ.get("MP_ACCESS_TOKEN")

    )

    try:

        payment_response = sdk.payment().get(payment_id)

        payment = payment_response["response"]

    except Exception:

        return redirect('/quiniela/')

    if payment.get("status") == "approved":

        perfil = request.user.perfil

        pago_existente = Perfil.objects.filter(

            mercadopago_payment_id=payment_id

        ).exclude(

            user__id=external_reference

        ).exists()

        if pago_existente:

            return HttpResponse(status=200)

        perfil.pago_confirmado = True

        perfil.participando = True

        perfil.fecha_pago = timezone.now()

        perfil.mercadopago_payment_id = payment_id

        perfil.tipo_pago = "mercadopago"

        perfil.save()

    return redirect('/quiniela/')


@login_required(login_url='/login/')
def pago_error(request):

    return redirect('/quiniela/')


@login_required(login_url='/login/')
def pago_pendiente(request):

    return redirect('/quiniela/')

def webhook_mercadopago(request):

    if request.method != "POST":

        return HttpResponse(status=400)

    payment_id = request.GET.get("data.id")

    if not payment_id:

        return HttpResponse(status=400)

    sdk = mercadopago.SDK(

        os.environ.get("MP_ACCESS_TOKEN")

    )

    try:

        payment_response = sdk.payment().get(

            payment_id

        )

        payment = payment_response["response"]

    except Exception:

        return HttpResponse(status=400)

    if payment.get("status") != "approved":

        return HttpResponse(status=200)

    external_reference = payment.get(

        "external_reference"

    )

    if not external_reference:

        return HttpResponse(status=400)

    try:

        perfil = Perfil.objects.get(

            user__id=external_reference

        )

    except Perfil.DoesNotExist:

        return HttpResponse(status=400)

    perfil.pago_confirmado = True

    perfil.participando = True

    perfil.fecha_pago = timezone.now()

    perfil.mercadopago_payment_id = payment_id

    perfil.tipo_pago = "mercadopago"

    perfil.save()

    return HttpResponse(status=200)