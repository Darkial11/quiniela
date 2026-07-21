"""quiniela / services

Logica de negocio reutilizable entre las vistas HTML y los endpoints de API.
"""
from .models import Pago, Pronostico
from usuarios.models import Perfil


def calcular_ranking(torneo_obj):
    """Calcula la tabla de posiciones de un torneo.

    Devuelve un dict con: primero, segundo, tercero, podio_total, resto.
    Cada entrada de esas listas es una tupla (nick, puntos).

    Esta es la misma logica que antes vivia dentro de la vista `ranking`
    en views.py, movida aqui para no duplicarla cuando se agrego el
    endpoint de API con la misma tabla.
    """
    tabla = {}
    if torneo_obj.tipo_cobro == "unico":
        for perfil in Perfil.objects.filter(pago_confirmado=True).select_related(
            "user"
        ):
            tabla[perfil.nick] = 0
        pronosticos = Pronostico.objects.select_related(
            "user__perfil", "partido"
        ).filter(
            user__perfil__pago_confirmado=True, partido__jornada__torneo=torneo_obj
        )
        for pronostico in pronosticos:
            nick = getattr(
                getattr(pronostico.user, "perfil", None),
                "nick",
                pronostico.user.username,
            )
            if nick not in tabla:
                tabla[nick] = 0
            if pronostico.partido.resultado_real == pronostico.seleccion:
                tabla[nick] += 1
    else:
        pagos_confirmados = Pago.objects.filter(
            jornada__torneo=torneo_obj, confirmado=True
        ).select_related("user__perfil")
        jornadas_pagadas = set()
        for pago in pagos_confirmados:
            nick = getattr(
                getattr(pago.user, "perfil", None), "nick", pago.user.username
            )
            if nick not in tabla:
                tabla[nick] = 0
            jornadas_pagadas.add((pago.user_id, pago.jornada_id))
        pronosticos = Pronostico.objects.select_related(
            "user__perfil", "partido"
        ).filter(partido__jornada__torneo=torneo_obj)
        for pronostico in pronosticos:
            clave = (pronostico.user_id, pronostico.partido.jornada_id)
            if clave not in jornadas_pagadas:
                continue
            nick = getattr(
                getattr(pronostico.user, "perfil", None),
                "nick",
                pronostico.user.username,
            )
            if pronostico.partido.resultado_real == pronostico.seleccion:
                tabla[nick] += 1

    ranking_ordenado = sorted(tabla.items(), key=lambda x: x[1], reverse=True)
    puntos_unicos = []
    for nombre, puntos in ranking_ordenado:
        if puntos not in puntos_unicos:
            puntos_unicos.append(puntos)

    primero = []
    segundo = []
    tercero = []
    if len(puntos_unicos) >= 1:
        primero = [j for j in ranking_ordenado if j[1] == puntos_unicos[0]]
    if len(puntos_unicos) >= 2:
        segundo = [j for j in ranking_ordenado if j[1] == puntos_unicos[1]]
    if len(puntos_unicos) >= 3:
        tercero = [j for j in ranking_ordenado if j[1] == puntos_unicos[2]]

    podio_total = len(primero) + len(segundo) + len(tercero)
    resto = ranking_ordenado[podio_total:]

    return {
        "primero": primero,
        "segundo": segundo,
        "tercero": tercero,
        "podio_total": podio_total,
        "resto": resto,
    }
