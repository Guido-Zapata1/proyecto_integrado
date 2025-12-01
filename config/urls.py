from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Rutas de Autenticación (Login, Logout)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Rutas de la aplicación 'reservas' (Namespace: reservas)
    path('reservas/', include('reservas.urls')),
    
    # Rutas de la aplicación 'inventario' (Namespace: inventario)
    path('inventario/', include('inventario.urls')),

    # Rutas Principales y Panel de Admin (Sin Namespace para ser globales)
    # Debe ir al final porque la ruta vacía '' captura el resto.
    path('', include('core.urls')),
]

# Configuración para servir imágenes en modo desarrollo (Debug=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


