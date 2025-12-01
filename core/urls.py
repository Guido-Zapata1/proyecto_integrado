from django.urls import path
from . import views

# Sin app_name para usar nombres globales

urlpatterns = [
    # === RUTA HOME (Dashboard General) ===
    path('', views.home, name='home'),

    # === ADMINISTRACIÓN ===
    path('administracion/', views.admin_dashboard, name='admin_dashboard'),

    # Gestión de Reservas (Torre de Control)
    path('administracion/reservas/', views.gestion_reservas, name='gestion_reservas'),
    path('administracion/reservas/aprobar/<int:reserva_id>/', views.aprobar_reserva, name='aprobar_reserva'),
    path('administracion/reservas/cancelar/<int:reserva_id>/', views.cancelar_forzosamente, name='cancelar_forzosamente'),
    path('administracion/reservas/exportar/', views.export_reservas_csv, name='export_reservas_csv'),

    # Gestión de Usuarios
    path('administracion/usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('administracion/usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('administracion/usuarios/estado/<int:user_id>/', views.gestionar_rol_estado, name='gestionar_rol_estado'),

    # Gestión de Inventario (Vistas de Admin)
    path('administracion/inventario/', views.gestion_inventario, name='gestion_inventario'),
    path('administracion/inventario/estado-espacio/<int:espacio_id>/', views.espacio_set_estado, name='espacio_set_estado'),
        # RUTA DEL NUEVO REPORTE EXCEL
    path('administracion/exportar/excel/', views.export_reservas_excel, name='export_reservas_excel'),
    
]


