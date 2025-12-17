from django.urls import path
from . import views

# --- ESTA LÍNEA ES LA QUE TE FALTA ---
app_name = 'inventario' 
# -------------------------------------

urlpatterns = [
    # Tus rutas de espacios
    path('espacios/', views.gestion_espacios, name='gestion_espacios'),
    path('espacios/editar/<int:espacio_id>/', views.editar_espacio, name='editar_espacio'),
    path('espacios/eliminar/<int:espacio_id>/', views.eliminar_espacio, name='eliminar_espacio'),

    # Tus rutas de recursos
    path('recursos/', views.gestion_recursos, name='gestion_recursos'),
    path('recursos/editar/<int:recurso_id>/', views.editar_recurso, name='editar_recurso'),
    path('recursos/eliminar/<int:recurso_id>/', views.eliminar_recurso, name='eliminar_recurso'),
]
