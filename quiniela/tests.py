"""quiniela / tests

Pruebas de los endpoints de API (DRF) agregados en el punto 2 del roadmap:
partidos por jornada, pronosticos propios del usuario, y ranking.
Tambien cubre guardar_pronosticos (vista HTML), incluyendo una prueba
de regresion para el bug de borrado de pronosticos al cerrar jornada.
"""
import json
import pytest
from django.contrib.auth.models import User

from .models import Torneo, Jornada, Partido, Pronostico, Pago
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


@pytest.mark.django_db
class TestGuardarPronosticosView:
    """POST /<torneo>/guardar/ - guarda (o reemplaza) los pronosticos
    del usuario para una jornada."""

    def test_guarda_pronosticos_con_jornada_abierta(
        self, client, torneo, jornada, partidos, usuario
    ):
        Perfil.objects.create(
            user=usuario, telefono="555", nick="Tester", participando=False
        )
        client.login(username="tester", password="clave12345")
        response = client.post(
            f"/{torneo.slug}/guardar/",
            data=json.dumps(
                {"pronosticos": [{"partido_id": partidos[0].id, "seleccion": "L"}]}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert Pronostico.objects.filter(user=usuario).count() == 1

    def test_no_borra_pronosticos_existentes_si_la_jornada_ya_cerro(
        self, client, torneo, jornada, partidos, usuario
    ):
        """Regresion: si el usuario ya tenia un pronostico guardado y la
        jornada se cierra, un intento posterior de guardado (ej. una
        pestana vieja con doble clic) no debe borrar lo que ya tenia."""
        Perfil.objects.create(
            user=usuario, telefono="555", nick="Tester", participando=False
        )
        client.login(username="tester", password="clave12345")

        primer_intento = client.post(
            f"/{torneo.slug}/guardar/",
            data=json.dumps(
                {"pronosticos": [{"partido_id": partidos[0].id, "seleccion": "L"}]}
            ),
            content_type="application/json",
        )
        assert primer_intento.status_code == 200
        assert Pronostico.objects.filter(user=usuario).count() == 1

        jornada.abierta = False
        jornada.save()

        segundo_intento = client.post(
            f"/{torneo.slug}/guardar/",
            data=json.dumps(
                {"pronosticos": [{"partido_id": partidos[0].id, "seleccion": "L"}]}
            ),
            content_type="application/json",
        )

        assert segundo_intento.json()["mensaje"] == "Jornada cerrada"
        assert Pronostico.objects.filter(user=usuario).count() == 1


@pytest.mark.django_db
class TestConfirmacionAutomaticaDePago:
    """Al guardar pronosticos, el pago debe quedar confirmado
    automaticamente, sin intervencion manual de un admin."""

    def test_torneo_pago_unico_confirma_perfil(
        self, client, torneo, jornada, partidos, usuario
    ):
        Perfil.objects.create(
            user=usuario,
            telefono="555",
            nick="Tester",
            participando=False,
            pago_confirmado=False,
        )
        client.login(username="tester", password="clave12345")

        response = client.post(
            f"/{torneo.slug}/guardar/",
            data=json.dumps(
                {"pronosticos": [{"partido_id": partidos[0].id, "seleccion": "L"}]}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        usuario.perfil.refresh_from_db()
        assert usuario.perfil.pago_confirmado is True
        assert usuario.perfil.fecha_pago is not None

    def test_torneo_pago_por_jornada_confirma_pago(self, client, usuario):
        Perfil.objects.create(
            user=usuario,
            telefono="555",
            nick="Tester",
            participando=False,
            pago_confirmado=False,
        )
        torneo_pj = Torneo.objects.create(
            nombre="Torneo Por Jornada",
            slug="torneo-por-jornada",
            tipo_cobro="por_jornada",
            activo=True,
        )
        jornada_pj = Jornada.objects.create(torneo=torneo_pj, numero=1, abierta=True)
        partido_pj = Partido.objects.create(
            local="Equipo A", visitante="Equipo B", grupo="A", jornada=jornada_pj
        )

        client.login(username="tester", password="clave12345")
        response = client.post(
            f"/{torneo_pj.slug}/guardar/",
            data=json.dumps(
                {"pronosticos": [{"partido_id": partido_pj.id, "seleccion": "L"}]}
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        pago = Pago.objects.get(user=usuario, jornada=jornada_pj)
        assert pago.confirmado is True
        assert pago.fecha_confirmacion is not None

    def test_no_desconfirma_un_pago_ya_confirmado_al_reguardar(
        self, client, usuario
    ):
        """Si el usuario edita su pronostico (vuelve a guardar) despues
        de que su pago ya estaba confirmado, el pago debe seguir
        confirmado, no revertirse."""
        Perfil.objects.create(
            user=usuario,
            telefono="555",
            nick="Tester",
            participando=False,
            pago_confirmado=False,
        )
        torneo_pj = Torneo.objects.create(
            nombre="Torneo Por Jornada 2",
            slug="torneo-por-jornada-2",
            tipo_cobro="por_jornada",
            activo=True,
        )
        jornada_pj = Jornada.objects.create(torneo=torneo_pj, numero=1, abierta=True)
        partido_pj = Partido.objects.create(
            local="Equipo A", visitante="Equipo B", grupo="A", jornada=jornada_pj
        )

        client.login(username="tester", password="clave12345")
        for seleccion in ["L", "V"]:
            response = client.post(
                f"/{torneo_pj.slug}/guardar/",
                data=json.dumps(
                    {
                        "pronosticos": [
                            {"partido_id": partido_pj.id, "seleccion": seleccion}
                        ]
                    }
                ),
                content_type="application/json",
            )
            assert response.status_code == 200

        pago = Pago.objects.get(user=usuario, jornada=jornada_pj)
        assert pago.confirmado is True
