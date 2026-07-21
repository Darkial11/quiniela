"""quiniela / tests

Pruebas de los endpoints de API (DRF) agregados en el punto 2 del roadmap:
partidos por jornada, pronosticos propios del usuario, y ranking.
"""
import pytest
from django.contrib.auth.models import User

from .models import Torneo, Jornada, Partido, Pronostico
from .services import calcular_ranking
from usuarios.models import Perfil


@pytest.fixture
def torneo():
    return Torneo.objects.create(
        nombre="Torneo Test", slug="torneo-test", tipo_cobro="unico", activo=True
    )


@pytest.fixture
def jornada(torneo):
    return Jornada.objects.create(torneo=torneo, numero=1, abierta=True)


@pytest.fixture
def partidos(jornada):
    p1 = Partido.objects.create(
        local="Equipo A",
        visitante="Equipo B",
        grupo="A",
        jornada=jornada,
        resultado_real="L",
    )
    p2 = Partido.objects.create(
        local="Equipo C",
        visitante="Equipo D",
        grupo="A",
        jornada=jornada,
        resultado_real="E",
    )
    return [p1, p2]


@pytest.fixture
def usuario():
    return User.objects.create_user(username="tester", password="clave12345")


@pytest.mark.django_db
class TestPartidosJornadaApi:
    """GET /<torneo>/api/jornada/<n>/partidos/ - es publico, sin login."""

    def test_devuelve_los_partidos_de_la_jornada(self, client, torneo, jornada, partidos):
        url = f"/{torneo.slug}/api/jornada/{jornada.numero}/partidos/"
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["local"] == "Equipo A"
        assert data[0]["visitante"] == "Equipo B"
        assert data[0]["resultado_real"] == "L"

    def test_torneo_inexistente_da_404(self, client):
        response = client.get("/no-existe/api/jornada/1/partidos/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestPronosticosPropiosApi:
    """GET /<torneo>/api/jornada/<n>/pronosticos/ - requiere login,
    y solo debe devolver los pronosticos del usuario que hizo la peticion."""

    def test_sin_login_responde_403(self, client, torneo, jornada):
        url = f"/{torneo.slug}/api/jornada/{jornada.numero}/pronosticos/"
        response = client.get(url)
        assert response.status_code == 403

    def test_solo_devuelve_los_pronosticos_del_usuario_logueado(
        self, client, torneo, jornada, partidos, usuario
    ):
        Pronostico.objects.create(user=usuario, partido=partidos[0], seleccion="L")

        otro_usuario = User.objects.create_user(username="otro", password="clave12345")
        Pronostico.objects.create(user=otro_usuario, partido=partidos[1], seleccion="V")

        client.login(username="tester", password="clave12345")
        url = f"/{torneo.slug}/api/jornada/{jornada.numero}/pronosticos/"
        response = client.get(url)

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["partido_id"] == partidos[0].id
        assert data[0]["seleccion"] == "L"


@pytest.mark.django_db
class TestRankingApi:
    """GET /<torneo>/api/ranking/ - requiere login."""

    def test_sin_login_responde_403(self, client, torneo):
        response = client.get(f"/{torneo.slug}/api/ranking/")
        assert response.status_code == 403

    def test_calcula_los_puntos_correctamente(
        self, client, torneo, jornada, partidos, usuario
    ):
        Perfil.objects.create(
            user=usuario,
            telefono="555",
            nick="TestNick",
            participando=True,
            pago_confirmado=True,
        )
        Pronostico.objects.create(user=usuario, partido=partidos[0], seleccion="L")  # acierta
        Pronostico.objects.create(user=usuario, partido=partidos[1], seleccion="V")  # falla

        client.login(username="tester", password="clave12345")
        response = client.get(f"/{torneo.slug}/api/ranking/")

        assert response.status_code == 200
        data = response.json()
        assert data["primero"] == [{"nick": "TestNick", "puntos": 1}]
        assert data["segundo"] == []
        assert data["tercero"] == []
        assert data["resto"] == []

    def test_torneo_inexistente_da_404(self, client, usuario):
        client.login(username="tester", password="clave12345")
        response = client.get("/no-existe/api/ranking/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestCalcularRankingService:
    """Prueba services.calcular_ranking directamente, sin pasar por HTTP,
    para aislar la logica de negocio de la capa de API."""

    def test_empate_en_primer_lugar(self, torneo, jornada, partidos, usuario):
        otro_usuario = User.objects.create_user(username="otro", password="clave12345")
        Perfil.objects.create(
            user=usuario, telefono="555", nick="Nick1",
            participando=True, pago_confirmado=True,
        )
        Perfil.objects.create(
            user=otro_usuario, telefono="555", nick="Nick2",
            participando=True, pago_confirmado=True,
        )
        # ambos aciertan el mismo partido -> empate en 1 punto
        Pronostico.objects.create(user=usuario, partido=partidos[0], seleccion="L")
        Pronostico.objects.create(user=otro_usuario, partido=partidos[0], seleccion="L")

        resultado = calcular_ranking(torneo)

        nicks_primero = {entrada[0] for entrada in resultado["primero"]}
        assert nicks_primero == {"Nick1", "Nick2"}
        assert resultado["segundo"] == []
