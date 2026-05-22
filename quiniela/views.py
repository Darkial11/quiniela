from django.contrib.auth.models import User

from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect

from django.http import JsonResponse

from .models import (

    Partido,

    Pronostico,

    Jornada

)

import json


@login_required(login_url='/login/')
def inicio(request, jornada=1):

    if not request.user.perfil.pago_confirmado:

        return redirect('/')

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