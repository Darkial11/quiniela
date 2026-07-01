from django.db import migrations


def crear_torneo_mundial(apps, schema_editor):
    Torneo = apps.get_model('quiniela', 'Torneo')
    Jornada = apps.get_model('quiniela', 'Jornada')

    torneo_mundial, creado = Torneo.objects.get_or_create(
        slug='mundial-2026',
        defaults={
            'nombre': 'Quiniela Mundial 2026',
            'tipo_cobro': 'unico',
            'activo': False,
        }
    )

    Jornada.objects.filter(torneo__isnull=True).update(torneo=torneo_mundial)


def revertir(apps, schema_editor):
    Torneo = apps.get_model('quiniela', 'Torneo')
    Jornada = apps.get_model('quiniela', 'Jornada')

    torneo_mundial = Torneo.objects.filter(slug='mundial-2026').first()
    if torneo_mundial:
        Jornada.objects.filter(torneo=torneo_mundial).update(torneo=None)
        torneo_mundial.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('quiniela', '0004_torneo_alter_jornada_numero_jornada_torneo_and_more'),
    ]

    operations = [
        migrations.RunPython(crear_torneo_mundial, revertir),
    ]