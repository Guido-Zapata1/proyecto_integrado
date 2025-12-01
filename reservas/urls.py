from django.urls import path
from . import views

# IMPORTANTE: Mantenemos el app_name porque ya corregimos los templates para usarlo
app_name = 'reservas'

urlpatterns = [
    # Ruta para listar (Mis Reservas)
    path('', views.listar_reservas, name='listar_reservas'),
    
    # Ruta para crear
    path('crear/', views.crear_reserva, name='crear_reserva'),
    
    # --- RUTAS DE GESTIÓN ---
    
    # Detalle: Ver información completa de una reserva
    path('detalle/<int:reserva_id>/', views.detalle_reserva, name='detalle'),
    
    # Editar: Modificar una reserva pendiente
    path('editar/<int:reserva_id>/', views.editar_reserva, name='editar'),
    
    # Cancelar: Borrar o cancelar una reserva
    path('cancelar/<int:reserva_id>/', views.cancelar_reserva, name='cancelar'),
    
    # --- RUTAS API (AJAX) ---
    
    # API para validar stock en tiempo real (usado al agregar recursos)
    path('api/consultar-stock/', views.api_consultar_stock, name='api_consultar_stock'),

    # API para alimentar el calendario visual (usado por FullCalendar)
    path('api/reservas-calendario/', views.api_reservas_calendario, name='api_reservas_calendario'),
]