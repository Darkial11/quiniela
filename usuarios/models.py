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

    def __str__(self):

        return self.nick