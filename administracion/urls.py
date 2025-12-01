from django.urls import path
from . import views

app_name = 'administracion'

urlpatterns = [
    path('', views.admin_dashboard, name='panel'),

    # Usuarios
    path('usuarios/', views.gestion_usuarios, name='lista_usuarios'),
    path('usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('usuarios/<int:user_id>/editar-rol/', views.editar_rol_usuario, name='editar_rol'),

    # Espacios
    path('espacios/', views.lista_espacios, name='lista_espacios'),
    path('espacios/crear/', views.crear_espacio, name='crear_espacio'),
    path('espacios/<int:id>/eliminar/', views.eliminar_espacio, name='eliminar_espacio'),

    # Recursos (ANTES INVENTARIO)
    path('recursos/', views.gestion_recursos, name='lista_recursos'),
    path('recursos/crear/', views.crear_recurso, name='crear_recurso'),
    path('recursos/<int:id>/eliminar/', views.eliminar_recurso, name='eliminar_recurso'),
    
]


