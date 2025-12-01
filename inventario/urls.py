from django.urls import path
from . import views

# Sin app_name para usar nombres globales y evitar errores de namespace
# Si tu base.html usa 'inventario:gestion_espacios', entonces descomenta la siguiente línea:
# app_name = 'inventario' 
# Pero para simplificar y coincidir con lo que hemos hablado, lo dejaremos global.

urlpatterns = [
    # === RUTAS DE ESPACIOS ===
    # Lista y Creación (Misma URL)
    path("espacios/", views.gestion_espacios, name="gestion_espacios"),
    # Edición
    path("espacios/editar/<int:espacio_id>/", views.editar_espacio, name="editar_espacio"),
    # Eliminación
    path("espacios/eliminar/<int:espacio_id>/", views.eliminar_espacio, name="eliminar_espacio"),

    # === RUTAS DE RECURSOS ===
    # Lista y Creación (Misma URL)
    path("recursos/", views.gestion_recursos, name="gestion_recursos"),
    # Edición
    path("recursos/editar/<int:recurso_id>/", views.editar_recurso, name="editar_recurso"),
    # Eliminación
    path("recursos/eliminar/<int:recurso_id>/", views.eliminar_recurso, name="eliminar_recurso"),
]
