from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

#IMPORTACIONES DE SEGURIDAD
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

@never_cache
def login_view(request):

    if request.user.is_authenticated:
        # Verificamos si en su sesión tiene la marca de "Mantener sesión"
        if request.session.get('keep_logged_in', False):
            # Si la casilla estaba marcada, lo devolvemos directo al dashboard
            return redirect('dashboard')
        else:
            # Si volvió atrás y la casilla NO estaba marcada, destruimos la sesión
            logout(request)

    if request.method == 'POST':
        correo = request.POST.get('emailInput')
        contrasena = request.POST.get('passwordInput')

        keep_logged_in = request.POST.get('keepLoggedIn')

        # Como el formulario usa Email, buscamos el nombre de usuario asociado a ese correo
        try:
            usuario_encontrado = User.objects.get(email=correo)
            # Autenticamos usando el username interno de Django
            user = authenticate(request, username=usuario_encontrado.username, password=contrasena)
            
            if user is not None:
                login(request, user) # Creamos la sesión segura en el navegador

                if keep_logged_in:
                    request.session['keep_logged_in'] = True
                    # La sesión durará 2 semanas (1209600 segundos)
                    request.session.set_expiry(1209600)
                else:
                    request.session['keep_logged_in'] = False
                    # La sesión expirará en cuanto se cierre el navegador
                    request.session.set_expiry(0)

                return redirect('dashboard')
            else:
                messages.error(request, 'Contraseña incorrecta. Inténtalo de nuevo.')
        except User.DoesNotExist:
            messages.error(request, 'Este correo electrónico no está registrado.')

    return render(request, 'accounts/login.html')

def register_view(request):
    if request.method == 'POST':
        nombre_usuario = request.POST.get('nameInput')
        nombres = request.POST.get('firstNameInput')
        apellidos = request.POST.get('lastNameInput')
        correo = request.POST.get('emailInput')
        contrasena = request.POST.get('passwordInput')

        # CREAMOS EL CONTEXTO: Guardamos las variables para poder devolverlas si hay error
        context = {
            'nombre_usuario': nombre_usuario,
            'nombres': nombres,
            'apellidos': apellidos,
            'correo': correo,
        }

        # 1. Comprobación: Usuario duplicado
        if User.objects.filter(username=nombre_usuario).exists():
            messages.error(request, 'El nombre de usuario ya está en uso. Por favor, elige otro.')
            return render(request, 'accounts/register.html', context) # <-- Pasamos el contexto

        # 2. Comprobación: Correo duplicado
        if User.objects.filter(email=correo).exists():
            messages.error(request, 'Este correo electrónico ya se encuentra registrado.')
            return render(request, 'accounts/register.html', context) # <-- Pasamos el contexto

        # 3. Comprobación: Fuerza de contraseña
        try:
            validate_password(contrasena)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return render(request, 'accounts/register.html', context) # <-- Pasamos el contexto

        # Si todo está bien, guardamos al usuario
        nuevo_usuario = User.objects.create_user(
            username=nombre_usuario, 
            email=correo, 
            password=contrasena,
            first_name=nombres,      
            last_name=apellidos      
        )
        nuevo_usuario.save() 
        
        messages.success(request, '¡Cuenta creada exitosamente! Ahora puedes iniciar sesión.')
        return redirect('login')

    # Si entran por primera vez (GET), el contexto va vacío
    return render(request, 'accounts/register.html')

@login_required
def dashboard_view(request):
    return render(request, 'accounts/dashboard.html')

# FUNCIONALIDAD: Destruye la sesión de usuario
def logout_view(request):
    logout(request)
    return redirect('login')

# VISTA DE PERFIL: Muestra los datos del usuario activo
@login_required
def profile_view(request):
    # 'request.user' contiene de manera automática toda la información del usuario logueado
    return render(request, 'accounts/profile.html')

def demo_view(request):
    return render(request, 'accounts/demo.html')

@login_required
def global_twins_view(request):
    return render(request, 'accounts/global-twins.html')