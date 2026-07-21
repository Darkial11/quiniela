"""quiniela / api_views

Endpoints de solo lectura con Django REST Framework. Reutilizan la misma
autenticacion por sesion que ya usa el sitio (el usuario tiene que haber
iniciado sesion por el login normal, no hay tokens nuevos).
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import Partido, Pronostico, Torneo
from .serializers import (
    PartidoSerializer,
    PronosticoPropioSerializer,
    RankingSerializer,
)
from .services import calcular_ranking


@api_view(["GET"])
@permission_classes([AllowAny])
def partidos_jornada_api(request, torneo_slug, jornada):
    """Partidos y resultados de una jornada. Es informacion publica,
    igual que la vista HTML `ver_pronosticos`, por eso no requiere login."""
    torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()
    if not torneo_obj:
        return Response(
            {"detail": "Torneo no encontrado"}, status=status.HTTP_404_NOT_FOUND
        )
    partidos = Partido.objects.filter(
        jornada__torneo=torneo_obj, jornada__numero=jornada
    ).order_by("id")
    serializer = PartidoSerializer(partidos, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def pronosticos_propios_api(request, torneo_slug, jornada):
    """Los pronosticos del usuario autenticado para una jornada.
    Mismo criterio de acceso que la vista `cargar_pronosticos` existente."""
    pronosticos = Pronostico.objects.filter(
        user=request.user,
        partido__jornada__torneo__slug=torneo_slug,
        partido__jornada__numero=jornada,
    )
    data = [
        {"partido_id": p.partido_id, "seleccion": p.seleccion} for p in pronosticos
    ]
    serializer = PronosticoPropioSerializer(data, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ranking_api(request, torneo_slug):
    """Tabla de posiciones del torneo. Mismo criterio de acceso
    (login requerido) que la vista HTML `ranking` existente."""
    torneo_obj = Torneo.objects.filter(slug=torneo_slug).first()
    if not torneo_obj:
        return Response(
            {"detail": "Torneo no encontrado"}, status=status.HTTP_404_NOT_FOUND
        )
    resultado = calcular_ranking(torneo_obj)
    data = {
        "primero": [{"nick": n, "puntos": p} for n, p in resultado["primero"]],
        "segundo": [{"nick": n, "puntos": p} for n, p in resultado["segundo"]],
        "tercero": [{"nick": n, "puntos": p} for n, p in resultado["tercero"]],
        "resto": [{"nick": n, "puntos": p} for n, p in resultado["resto"]],
    }
    serializer = RankingSerializer(data)
    return Response(serializer.data)
