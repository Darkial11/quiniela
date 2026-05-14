from django.core.management.base import BaseCommand

from quiniela.models import (

    Jornada,

    Partido

)

from datetime import date, time


class Command(BaseCommand):

    help = 'Carga partidos del Mundial 2026'


    def handle(self, *args, **kwargs):

        jornada1, _ = Jornada.objects.get_or_create(

            numero=1

        )

        jornada2, _ = Jornada.objects.get_or_create(

            numero=2

        )

        jornada3, _ = Jornada.objects.get_or_create(

            numero=3

        )

        partidos = [

            # JORNADA 1

            {

                'local': 'México',

                'visitante': 'Estados Unidos',

                'grupo': 'A',

                'jornada': jornada1,

                'fecha_partido': date(2026, 6, 11),

                'hora_partido': time(19, 0),

                'estadio': 'Estadio Azteca',

                'ciudad': 'Ciudad de México',

                'pais_sede': 'México'

            },

            {

                'local': 'Argentina',

                'visitante': 'Japón',

                'grupo': 'B',

                'jornada': jornada1,

                'fecha_partido': date(2026, 6, 12),

                'hora_partido': time(16, 0),

                'estadio': 'MetLife Stadium',

                'ciudad': 'New Jersey',

                'pais_sede': 'Estados Unidos'

            },

            {

                'local': 'Francia',

                'visitante': 'Canadá',

                'grupo': 'C',

                'jornada': jornada1,

                'fecha_partido': date(2026, 6, 12),

                'hora_partido': time(20, 0),

                'estadio': 'BMO Field',

                'ciudad': 'Toronto',

                'pais_sede': 'Canadá'

            },

            {

                'local': 'Brasil',

                'visitante': 'Alemania',

                'grupo': 'D',

                'jornada': jornada1,

                'fecha_partido': date(2026, 6, 13),

                'hora_partido': time(18, 0),

                'estadio': 'SoFi Stadium',

                'ciudad': 'Los Ángeles',

                'pais_sede': 'Estados Unidos'

            },

            # JORNADA 2

            {

                'local': 'México',

                'visitante': 'Japón',

                'grupo': 'A',

                'jornada': jornada2,

                'fecha_partido': date(2026, 6, 16),

                'hora_partido': time(19, 0),

                'estadio': 'Akron Stadium',

                'ciudad': 'Guadalajara',

                'pais_sede': 'México'

            },

            {

                'local': 'Estados Unidos',

                'visitante': 'Argentina',

                'grupo': 'B',

                'jornada': jornada2,

                'fecha_partido': date(2026, 6, 16),

                'hora_partido': time(20, 0),

                'estadio': 'AT&T Stadium',

                'ciudad': 'Dallas',

                'pais_sede': 'Estados Unidos'

            },

            {

                'local': 'Canadá',

                'visitante': 'Francia',

                'grupo': 'C',

                'jornada': jornada2,

                'fecha_partido': date(2026, 6, 17),

                'hora_partido': time(17, 0),

                'estadio': 'BC Place',

                'ciudad': 'Vancouver',

                'pais_sede': 'Canadá'

            },

            {

                'local': 'Alemania',

                'visitante': 'Brasil',

                'grupo': 'D',

                'jornada': jornada2,

                'fecha_partido': date(2026, 6, 17),

                'hora_partido': time(21, 0),

                'estadio': 'NRG Stadium',

                'ciudad': 'Houston',

                'pais_sede': 'Estados Unidos'

            },

            # JORNADA 3

            {

                'local': 'México',

                'visitante': 'Argentina',

                'grupo': 'A',

                'jornada': jornada3,

                'fecha_partido': date(2026, 6, 22),

                'hora_partido': time(20, 0),

                'estadio': 'Estadio BBVA',

                'ciudad': 'Monterrey',

                'pais_sede': 'México'

            },

            {

                'local': 'Estados Unidos',

                'visitante': 'Japón',

                'grupo': 'B',

                'jornada': jornada3,

                'fecha_partido': date(2026, 6, 22),

                'hora_partido': time(18, 0),

                'estadio': 'Lumen Field',

                'ciudad': 'Seattle',

                'pais_sede': 'Estados Unidos'

            },

            {

                'local': 'Francia',

                'visitante': 'Alemania',

                'grupo': 'C',

                'jornada': jornada3,

                'fecha_partido': date(2026, 6, 23),

                'hora_partido': time(19, 0),

                'estadio': 'Mercedes-Benz Stadium',

                'ciudad': 'Atlanta',

                'pais_sede': 'Estados Unidos'

            },

            {

                'local': 'Brasil',

                'visitante': 'Canadá',

                'grupo': 'D',

                'jornada': jornada3,

                'fecha_partido': date(2026, 6, 23),

                'hora_partido': time(21, 0),

                'estadio': 'Hard Rock Stadium',

                'ciudad': 'Miami',

                'pais_sede': 'Estados Unidos'

            }

        ]

        for partido in partidos:

            Partido.objects.get_or_create(

                local=partido['local'],

                visitante=partido['visitante'],

                defaults={

                    'grupo': partido['grupo'],

                    'jornada': partido['jornada'],

                    'fecha_partido': partido['fecha_partido'],

                    'hora_partido': partido['hora_partido'],

                    'estadio': partido['estadio'],

                    'ciudad': partido['ciudad'],

                    'pais_sede': partido['pais_sede']

                }

            )

        self.stdout.write(

            self.style.SUCCESS(

                'Partidos cargados correctamente'

            )

        )