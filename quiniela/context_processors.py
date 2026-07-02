""" quiniela / context_processors """
from .models import Torneo


def torneo_actual(request):

    torneo = None

    if request.resolver_match:

        torneo_slug = request.resolver_match.kwargs.get('torneo_slug')

        if torneo_slug:

            torneo = Torneo.objects.filter(slug=torneo_slug).first()

    return {
        'torneo_actual': torneo
    }
