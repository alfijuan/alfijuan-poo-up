from django.contrib.auth import logout, authenticate, login
from django.http import JsonResponse, Http404, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from api.helpers import get_request_body
from django.contrib.auth.models import User
from api.models import Turn, Reservation
from datetime import date, datetime
from django.shortcuts import get_object_or_404
import csv

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            post = get_request_body(request)
            if not post.get('username', None) or not post.get('password', None):
                return JsonResponse({'message': "El usuario y contraseña son requeridos"}, status=400)
            user = authenticate(request, username=post.get('username'), password=post.get('password'))
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return JsonResponse(user.profile.to_json(), status=200)
                return JsonResponse({'message': "El usuario no esta habilitado"}, status=400)
            return JsonResponse({'message': "Los datos ingresados no son válidos"}, status=400)
        else:
            return JsonResponse(request.user.profile.to_json(), status=200)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)


@csrf_exempt
def api_me(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            return JsonResponse(request.user.profile.to_json(), status=200)
        else:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)
    if request.method == 'PATCH':
        if request.user.is_authenticated:
            data = get_request_body(request)
            request.user.first_name = data.get("first_name")
            request.user.last_name = data.get("last_name")
            request.user.profile.full_name = f'{data.get("first_name")} {data.get("last_name")}'
            if data.get("dni"):
                request.user.profile.dni = data.get("dni")
            request.user.save()
            return JsonResponse(request.user.profile.to_json(), status=200)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_logout(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request)
            return JsonResponse({'message': "Usuario deslogueado"})
        return JsonResponse({'message': "No hay usuario logueado", "code": "no_logged_user"}, status=400)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_signup(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            post = get_request_body(request)
            if not post.get('password', None) or not post.get('username', None) or not post.get('passwordB', None):
                return JsonResponse({'message': "El usuario y contraseña son requeridos"}, status=400)
            if post['password'] == post['passwordB']:
                try:
                    user = User.objects.get(username=post['username'])
                    return JsonResponse({'message': "El email ya esta asociado a una cuenta"}, status=400)
                except:
                    user = User.objects.create_user(post['username'], post['username'], post['password'])
                    user.email = post.get('username')
                    user.profile.type_id = '0000'
                    user.profile.pathology = post.get('pathology', '')
                    user.profile.turn_time = post.get('turn_time', '')
                    user.save()
                    login(request, user)
                    return JsonResponse(user.profile.to_json(), status=200)
            return JsonResponse({'message': "Las contraseñas no coinciden"}, status=400)
        return JsonResponse({'message': "Ya hay un usuario logueado"}, status=400)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_therapists(request):
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)
        therapists = User.objects.filter(profile__type_id="2002")
        return JsonResponse([x.profile.to_json() for x in therapists], status=200, safe=False)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_turns_by_therapist(request, id):
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)

        if not request.GET.get('start_time') or not request.GET.get('end_time'):
            return JsonResponse({'message': "start_time y end_time son requeridos para la busqueda de turnos"}, status=400)
        try:
            therapist = User.objects.filter(profile__type_id="2002").get(id=id)
        except:
            raise Http404
        # Obtengo los turnos de un terapista
        turns = Turn.objects.filter(therapist=therapist)

        try:
            date_from = datetime.strptime(request.GET.get('start_time', None), '%d/%m/%y')
            turns = turns.filter(start_time__gte=date_from)
        except:
            return JsonResponse({'message': "Fecha de inicio no valida, el formato debe ser DD/MM/YY"}, status=400)
        
        try:
            date_to = datetime.strptime(request.GET.get('end_time', None), '%d/%m/%y')
            turns = turns.filter(end_time__lte=date_to)
        except:
            return JsonResponse({'message': "Fecha de fin no valida, el formato debe ser DD/MM/YY"}, status=400)
        # Si no es admin, solo le muestro los habilitados
        if not request.user.profile.type_id == "3003":
            turns = turns.filter(available=True)
        return JsonResponse([x.to_json() for x in turns], status=200, safe=False)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_assign_turn(request, turn):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)
        # Busco turno
        try:
            turn = Turn.objects.get(id=turn)
        except:
            return JsonResponse({'message': "El turno no existe", 'code': 'not_found'}, status=404)
        if not turn.available:
            return JsonResponse({'message': "El turno ya esta asignado"}, status=400)
        # Si es admin, asigno el user que me envia via data
        user = request.user
        if request.user.profile.type_id == "3003":
            data = get_request_body(request)
            if not data.get('user', None):
                return JsonResponse({'message': "El id del usuario es requerido"}, status=400)
            try:
                user = User.objects.get(id=data.get('user', None))
            except:
                return JsonResponse({'message': "El usuario no existe", 'code': 'not_found'}, status=404)
        if Reservation.objects.filter(status="", pacient=user).count() >= 2:
            return JsonResponse({'message': "El paciente ya posee un turno reservado"}, status=400)
        r = Reservation(
            turn=turn,
            pacient=user,
            status=""
        )
        r.save()
        turn.available = False
        turn.save()
        return JsonResponse(r.to_json(), status=200, safe=False)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_create_turns(request, id, date):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)
        if not request.user.profile.type_id == "3003":
            raise Http404
        # Obtengo terapista
        try:
            therapist = User.objects.filter(profile__type_id="2002").get(id=id)
        except:
            raise Http404
        
@csrf_exempt
def api_turns(request):
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)

        if not request.GET.get('start_time') or not request.GET.get('end_time'):
            return JsonResponse({'message': "start_time y end_time son requeridos para la busqueda de turnos"}, status=400)
        # Obtengo los turnos de un terapista
        turns = Turn.objects.all()

        try:
            date_from = datetime.strptime(f"{request.GET.get('start_time', None)} 00:00:00", '%d/%m/%y %H:%M:%S')
            turns = turns.filter(start_time__gte=date_from)
        except:
            return JsonResponse({'message': "Fecha de inicio no valida, el formato debe ser DD/MM/YY"}, status=400)
        
        try:
            date_to = datetime.strptime(f"{request.GET.get('end_time', None)} 23:59:59", '%d/%m/%y %H:%M:%S')
            turns = turns.filter(end_time__lte=date_to)
        except:
            return JsonResponse({'message': "Fecha de fin no valida, el formato debe ser DD/MM/YY"}, status=400)
        # Si no es admin, solo le muestro los habilitados
        if not request.user.profile.type_id == "3003":
            turns = turns.filter(available=True)
        return JsonResponse([x.to_json() for x in turns], status=200, safe=False)
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)
        date
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_reservations(request):
    if request.method == 'GET':
        if not request.user.is_authenticated:
            return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)

        # Obtengo las reservas
        reservations = Reservation.objects.all()
        if not request.user.profile.type_id == "3003":
            reservations = Reservation.objects.filter(pacient=request.user)

        return JsonResponse([x.to_json() for x in reservations], status=200, safe=False)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_reservations_info(request, id):
    if not request.user.is_authenticated:
        return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)
    
    reservations = Reservation.objects.all()
    if not request.user.profile.type_id == "3003":
        reservations = Reservation.objects.filter(pacient=request.user)
    r = get_object_or_404(reservations, id=id)

    if request.method == 'GET':
        # Obtengo la reserva
        return JsonResponse(r.to_json(), status=200, safe=False)
    
    if request.method == 'PATCH':
        if r.turn.start_time.date() == datetime.today().date():
            return JsonResponse({'message': "No se puede cancelar un turno el mismo dia",}, status=400)
        r.status = "CANCELED"
        r.turn.available = True
        r.save()
        return JsonResponse(r.to_json(), status=200, safe=False)
    return JsonResponse({'message': "Método no permitido", "code": "method_not_allowed"}, status=400)

@csrf_exempt
def api_reservations_export(request):
    if not request.user.is_authenticated:
        return JsonResponse({'message': "No hay usuario logueado", 'code': 'no_logged_user'}, status=200)
    
    reservations = Reservation.objects.all()
    if not request.user.profile.type_id == "3003":
        reservations = reservations.filter(pacient=request.user)
    
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'},
    )

    writer = csv.writer(response)
    for x in reservations:
        writer.writerow([x.id, x.turn.start_time, x.turn.therapist.last_name, x.status])

    return response