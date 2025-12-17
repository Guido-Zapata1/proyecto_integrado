from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

def admin_required(view_func):
    """
    Decorador que verifica si el usuario es ADMINISTRADOR.
    Si no lo es, lo redirige al home o lanza error 403.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verificar si está logueado
        if not request.user.is_authenticated:
            return redirect('login')
        
        # Verificar rol
        # Asumimos que tu modelo de usuario tiene el campo 'rol'
        if getattr(request.user, 'rol', '') == 'ADMIN' or request.user.is_superuser:
            return view_func(request, *args, **kwargs)
        
        # Si es usuario normal, lo mandamos a su home
        return redirect('home')
        
    return _wrapped_view