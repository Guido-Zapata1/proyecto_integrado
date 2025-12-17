from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# ==============================================================================
# CONFIGURACIÓN DE LA API (ROUTER)
# ==============================================================================
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'areas', views.AreaViewSet, basename='area')
router.register(r'carreras', views.CarreraViewSet, basename='carrera')

# ==============================================================================
# RUTAS URL
# ==============================================================================

urlpatterns = [
    # === RUTA HOME (Dashboard General) ===
    path('', views.home, name='home'),

    # === ADMINISTRACIÓN DASHBOARD ===
    path('administracion/', views.admin_dashboard, name='admin_dashboard'),

    # === GESTIÓN DE RESERVAS ===
    path('administracion/reservas/', views.gestion_reservas, name='gestion_reservas'),
    path('administracion/reservas/aprobar/<int:reserva_id>/', views.aprobar_reserva, name='aprobar_reserva'),
    path('administracion/reservas/cancelar/<int:reserva_id>/', views.cancelar_forzosamente, name='cancelar_forzosamente'),
    path('administracion/reservas/exportar/', views.export_reservas_csv, name='export_reservas_csv'),
    path('administracion/reservas/exportar/excel/', views.export_reservas_excel, name='export_reservas_excel'),

    # === GESTIÓN DE USUARIOS ===
    path('administracion/usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('administracion/usuarios/crear/', views.crear_usuario, name='crear_usuario'),
    path('administracion/usuarios/editar/<int:user_id>/', views.editar_usuario, name='editar_usuario'),
    path('administracion/usuarios/estado/<int:user_id>/', views.gestionar_rol_estado, name='gestionar_rol_estado'),

    # === GESTIÓN DE ÁREAS ===
    path('administracion/areas/', views.gestion_areas, name='gestion_areas'),
    path('administracion/areas/crear/', views.crear_area, name='crear_area'),
    path('administracion/areas/editar/<int:area_id>/', views.editar_area, name='editar_area'),
    path('administracion/areas/eliminar/<int:area_id>/', views.eliminar_area, name='eliminar_area'),

    # === GESTIÓN DE CARRERAS ===
    path('administracion/carreras/', views.gestion_carreras, name='gestion_carreras'),
    path('administracion/carreras/crear/', views.crear_carrera, name='crear_carrera'),
    path('administracion/carreras/editar/<int:carrera_id>/', views.editar_carrera, name='editar_carrera'),
    path('administracion/carreras/eliminar/<int:carrera_id>/', views.eliminar_carrera, name='eliminar_carrera'),

    # === GESTIÓN DE INVENTARIO (Aquí estaban faltando rutas) ===
    path('administracion/inventario/', views.gestion_inventario, name='gestion_inventario'),
    path('administracion/inventario/recurso/editar/<int:recurso_id>/', views.editar_recurso, name='editar_recurso'),
    path('administracion/inventario/recurso/eliminar/<int:recurso_id>/', views.eliminar_recurso, name='eliminar_recurso'),
    path('administracion/inventario/estado-espacio/<int:espacio_id>/', views.espacio_set_estado, name='espacio_set_estado'),

    # === APIs INTERNAS ===
    path('api/stock-check/', views.api_stock_actual, name='api_stock_actual'),
    path('api/reservas-calendario/', views.api_reservas_calendario, name='api_reservas_calendario'),

    # === RUTAS DE LA API REST (React) ===
    path('api/', include(router.urls)),
    path("notificaciones/", include("notificaciones.urls")),
]