""" quiniela /models """
from django.db import models
from django.contrib.auth.models import User


class Torneo(models.Model):

    TIPO_COBRO_CHOICES = [
        ('unico', 'Pago único'),
        ('por_jornada', 'Pago por jornada'),
    ]

    nombre = models.CharField(max_length=100)

    slug = models.SlugField(max_length=100, unique=True)

    tipo_cobro = models.CharField(
        max_length=20,
        choices=TIPO_COBRO_CHOICES
    )

    activo = models.BooleanField(default=True)

    def __str__(self):

        return self.nombre


class Jornada(models.Model):

    torneo = models.ForeignKey(
        Torneo,
        on_delete=models.CASCADE
    )

    numero = models.IntegerField()

    abierta = models.BooleanField(default=True)

    class Meta:
        unique_together = ('torneo', 'numero')

    def __str__(self):

        return f"Jornada {self.numero} - {self.torneo.nombre if self.torneo else 'sin torneo'}"


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

class Pago(models.Model):

    METODO_CHOICES = [
        ('transferencia', 'Transferencia'),
        ('efectivo', 'Efectivo'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    jornada = models.ForeignKey(
        Jornada,
        on_delete=models.CASCADE
    )

    monto = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=30.00
    )

    metodo = models.CharField(
        max_length=20,
        choices=METODO_CHOICES,
        null=True,
        blank=True
    )

    confirmado = models.BooleanField(default=False)

    fecha_confirmacion = models.DateTimeField(
        null=True,
        blank=True
    )

    confirmado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pagos_confirmados'
    )

    class Meta:
        unique_together = ('user', 'jornada')

    def __str__(self):

        return f"{self.user.username} - {self.jornada}"