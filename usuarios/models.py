""" usuarios /models """
from django.db import models

from django.contrib.auth.models import User


class Perfil(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    telefono = models.CharField(
        max_length=20
    )

    nick = models.CharField(
        max_length=50,
        unique=True
    )

    participando = models.BooleanField(
        default=False
    )

    pago_confirmado = models.BooleanField(
        default=False
    )

    fecha_pago = models.DateTimeField(
        null=True,
        blank=True
    )

    mercadopago_payment_id = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    tipo_pago = models.CharField(
        max_length=30,
        default="mercadopago"
    )

    def __str__(self):

        return self.nick