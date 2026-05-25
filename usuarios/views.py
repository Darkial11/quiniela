from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from quiniela.models import Partido, Jornada, Pronostico
from .models import Perfil

def registro(request):

    if request.method == 'POST':

        if not request.POST.get(

            'acepta_reglamento'

            ):

            return render(

            request,

            'usuarios/registro.html',

            {

                'error': '''

                Debes aceptar el reglamento

                '''

            }

        )

        nombre = request.POST['nombre']

        apellido = request.POST['apellido']

        email = request.POST['email']

        telefono = request.POST['telefono']

        nick = request.POST['nick'].upper()

        if not nick.replace('_', '').isalnum():

            return render(

                request,

                'usuarios/registro.html',

                {

                    'error': '''
                    El nick solo puede contener:
                    letras, números y _
                    '''

                }

            )

        password = request.POST['password']

        if User.objects.filter(username=nick).exists():

            return render(

                request,

                'usuarios/registro.html',

                {

                    'error': 'Ese nick ya está registrado'

                }

            )
        
        if User.objects.filter(email=email).exists():

            return render(

                request,

                'usuarios/registro.html',

                {

                    'error': 'Ese correo ya está registrado'

                }

            )

        user = User.objects.create_user(

            username=nick,

            email=email,

            password=password,

            first_name=nombre,

            last_name=apellido

        )

        Perfil.objects.create(

            user=user,

            telefono=telefono,

            nick=nick

        )

        login(request, user)

        return redirect('/quiniela/')

    return render(

        request,

        'usuarios/registro.html'

    )

def iniciar_sesion(request):

    mensaje = ''

    if request.method == 'POST':

        username = request.POST['username'].upper()

        password = request.POST['password']

        user = authenticate(

            request,

            username=username,

            password=password

        )

        if user is not None:

            login(request, user)

            return redirect('/quiniela/')

        else:

            mensaje = 'Usuario o contraseña incorrectos'

    return render(

        request,

        'usuarios/login.html',

        {

            'mensaje': mensaje

        }

    )


def cerrar_sesion(request):

    logout(request)

    return redirect('/')


def home(request):

    participantes = Perfil.objects.filter(

    participando=True

).count()

    partidos = Partido.objects.count()

    resultados = Partido.objects.exclude(
        resultado_real__isnull=True
    ).exclude(
        resultado_real=''
    ).count()

    context = {

        'participantes': participantes,
        'partidos': partidos,
        'resultados': resultados,

    }

    return render(
        request,
        'usuarios/home.html',
        context
    )

@login_required(login_url='/login/')
def dashboard(request):

    user = request.user

    nick_usuario = getattr(
        getattr(user, 'perfil', None),
        'nick',
        user.username
    )

    # Jornada activa dinámica
    jornada_activa = Jornada.objects.filter(
        abierta=True
    ).order_by('numero').first()

    # Query eficiente para pronósticos del usuario
    pronosticos = Pronostico.objects.filter(
        user=user
    ).select_related('partido')

    total_pronosticos = pronosticos.count()

    total_aciertos = sum(
        1 for p in pronosticos
        if p.seleccion == p.partido.resultado_real
    )

    # Query eficiente para ranking global
    todos = Pronostico.objects.select_related(
        'user__perfil',
        'partido'
    ).all()

    ranking = {}

    for item in todos:

        nick = getattr(
            getattr(item.user, 'perfil', None),
            'nick',
            item.user.username
        )

        if nick not in ranking:

            ranking[nick] = 0

        if item.seleccion == item.partido.resultado_real:

            ranking[nick] += 1

    ranking_ordenado = sorted(
        ranking.items(),
        key=lambda x: x[1],
        reverse=True
    )

    posicion = next(
        (i + 1 for i, item in enumerate(ranking_ordenado)
         if item[0] == nick_usuario),
        1
    )

    top5 = ranking_ordenado[:5]

    return render(
        request,
        'usuarios/dashboard.html',
        {
            'total_pronosticos': total_pronosticos,
            'total_aciertos': total_aciertos,
            'posicion': posicion,
            'top5': top5,
            'jornada_activa': jornada_activa
        }
    )

def reglamento(request):

    return render(

        request,

        'usuarios/reglamento.html'

    )

def contacto(request):

    return render(

        request,

        "usuarios/contacto.html"

    )
