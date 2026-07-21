"""quiniela / serializers"""
from rest_framework import serializers

from .models import Partido


class PartidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Partido
        fields = [
            "id",
            "local",
            "visitante",
            "grupo",
            "fecha_partido",
            "hora_partido",
            "estadio",
            "ciudad",
            "pais_sede",
            "resultado_real",
        ]


class PronosticoPropioSerializer(serializers.Serializer):
    """No es un ModelSerializer porque el shape (partido_id, seleccion)
    es el mismo que ya devuelve la vista `cargar_pronosticos` existente,
    para no cambiar el contrato que el frontend actual ya conoce."""

    partido_id = serializers.IntegerField()
    seleccion = serializers.CharField()


class RankingEntradaSerializer(serializers.Serializer):
    nick = serializers.CharField()
    puntos = serializers.IntegerField()


class RankingSerializer(serializers.Serializer):
    """Espeja la estructura que ya devuelve services.calcular_ranking:
    grupos de podio (con empates) mas el resto de participantes."""

    primero = RankingEntradaSerializer(many=True)
    segundo = RankingEntradaSerializer(many=True)
    tercero = RankingEntradaSerializer(many=True)
    resto = RankingEntradaSerializer(many=True)
