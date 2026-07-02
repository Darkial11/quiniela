from django.core.management.base import BaseCommand
from quiniela.models import Torneo, Jornada, Partido
from datetime import date, datetime
import pandas as pd
import os


MESES = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}


def parsear_fecha(texto):

    limpio = texto.lower().replace(' de ', ' ')

    dia, mes_nombre, anio = limpio.split()

    return date(int(anio), MESES[mes_nombre], int(dia))


class Command(BaseCommand):

    help = 'Importa partidos de Liga MX Apertura 2026 desde Excel'

    def handle(self, *args, **kwargs):

        torneo_obj, torneo_creado = Torneo.objects.get_or_create(
            slug='apertura-2026',
            defaults={
                'nombre': 'Liga MX - Apertura 2026',
                'tipo_cobro': 'por_jornada',
                'activo': False,
            }
        )

        ruta_excel = os.path.join('data', 'liga-mx.xlsx')

        df = pd.read_excel(ruta_excel, sheet_name='Apertura2026')

        contador = 0

        for _, fila in df.iterrows():

            jornada_obj, _ = Jornada.objects.get_or_create(
                torneo=torneo_obj,
                numero=int(fila['Jornada']),
                defaults={'abierta': True}
            )

            fecha_partido = parsear_fecha(str(fila['Fecha_partido']))

            texto_hora = str(fila['Hora_partido']).strip()

            try:
                hora_partido = datetime.strptime(texto_hora, '%H:%M').time()
            except ValueError:
                hora_partido = None
                self.stdout.write(
                    self.style.WARNING(
                        f'Hora no definida para {fila["Local"]} vs {fila["Visitante"]} (Jornada {fila["Jornada"]}): "{texto_hora}"'
                    )
                )

            resultado_real = fila['Resultado real']

            if pd.isna(resultado_real):
                resultado_real = None

            Partido.objects.update_or_create(
                jornada=jornada_obj,
                local=fila['Local'],
                visitante=fila['Visitante'],
                defaults={
                    'grupo': 'LIGA MX',
                    'fecha_partido': fecha_partido,
                    'hora_partido': hora_partido,
                    'estadio': fila['Estadio'],
                    'ciudad': fila['Ciudad'],
                    'pais_sede': fila['Pais sede'],
                    'resultado_real': resultado_real,
                }
            )

            contador += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'{contador} partidos de Liga MX importados. Torneo creado: {torneo_creado}'
            )
        )
