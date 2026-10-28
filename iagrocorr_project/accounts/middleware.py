from django.utils.cache import add_never_cache_headers


class NoCacheParaUsuariosAutenticadosMiddleware:
    """
    Evita que el navegador guarde en caché las páginas vistas con sesión iniciada.

    Sin esto, después de cerrar sesión el botón "Atrás" del navegador muestra
    la copia guardada del dashboard (u otra página privada) sin pasar por el
    servidor. Con estas cabeceras el navegador vuelve a pedir la página, y como
    ya no hay sesión, @login_required redirige al login.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, 'user', None)
        if user is not None and user.is_authenticated:
            add_never_cache_headers(response)
        return response
