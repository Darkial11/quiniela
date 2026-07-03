""" quiniela / context_processors """
from .models import Torneo


def torneo_actual(request):

    torneo = None

    if request.resolver_match:

        torneo_slug = request.resolver_match.kwargs.get('torneo_slug')

        if torneo_slug:

            torneo = Torneo.objects.filter(slug=torneo_slug).first()

            if torneo:
                request.session['ultimo_torneo_slug'] = torneo.slug

    if not torneo:

        ultimo_slug = request.session.get('ultimo_torneo_slug')

        if ultimo_slug:

            torneo = Torneo.objects.filter(slug=ultimo_slug).first()

    if not torneo:

        torneo = Torneo.objects.filter(activo=True).first()

    return {
        'torneo_actual': torneo
    }
