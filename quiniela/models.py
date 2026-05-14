""" quiniela /models """
from django.db import models
from django.contrib.auth.models import User


class Jornada(models.Model):

    numero = models.IntegerField(unique=True)

    abierta = models.BooleanField(default=True)

    def __str__(self):

        return f"Jornada {self.numero}"


class Partido(models.Model):

    local = models.CharField(

        max_length=100

    )

    visitante = models.CharField(

        max_length=100

    )

    grupo = models.CharField(

        max_length=10

    )

    jornada = models.ForeignKey(

        Jornada,

        on_delete=models.CASCADE,

        null=True,

        blank=True

    )

    fecha_partido = models.DateField(

        null=True,

        blank=True

    )

    hora_partido = models.TimeField(

        null=True,

        blank=True

    )

    estadio = models.CharField(

        max_length=200,

        blank=True,

        null=True

    )

    ciudad = models.CharField(

        max_length=100,

        blank=True,

        null=True

    )

    pais_sede = models.CharField(

        max_length=100,

        blank=True,

        null=True

    )

    resultado_real = models.CharField(

        max_length=1,

        blank=True,

        null=True

    )

    fecha_creacion = models.DateTimeField(

        auto_now_add=True

    )

    def __str__(self):

        return f"{self.local} vs {self.visitante}"


class Pronostico(models.Model):

    user = models.ForeignKey(

        User,

        on_delete=models.CASCADE

    )

    partido = models.ForeignKey(

        Partido,

        on_delete=models.CASCADE

    )

    seleccion = models.CharField(

        max_length=1

    )

    def __str__(self):

        return f'''

        {self.user.username}

        -

        {self.partido}

        '''
