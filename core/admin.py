from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Area, Carrera

# 1. Configuración para Áreas
@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion', 'total_carreras')
    search_fields = ('nombre',)
    
    # Muestra cuántas carreras tiene asociadas
    def total_carreras(self, obj):
        return obj.carreras.count()
    total_carreras.short_description = 'N° Carreras'

# 2. Configuración para Carreras
@admin.register(Carrera)
class CarreraAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'area')
    list_filter = ('area',) # Filtro lateral
    search_fields = ('nombre', 'codigo')
    autocomplete_fields = ['area'] # Útil para buscar el área si hay muchas

# 3. Configuración para tu Usuario Personalizado
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # Definimos el orden por email ya que no existe username
    ordering = ['email']
    
    # Columnas que se ven en la tabla de usuarios
    list_display = ('email', 'first_name', 'last_name', 'rol', 'get_carrera', 'get_area', 'is_staff')
    
    # Filtros laterales
    list_filter = ('rol', 'is_staff', 'is_superuser', 'carrera__area', 'carrera')
    
    # Campos de búsqueda
    search_fields = ('email', 'first_name', 'last_name', 'rut', 'carrera__nombre')

    # Organización del formulario de edición de usuario
    # Eliminamos 'username' y agregamos 'rol', 'rut', 'carrera'
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'rut', 'rol')}),
        ('Información Académica', {'fields': ('carrera',)}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login', 'date_joined')}),
    )

    # Configuración para el formulario de "Agregar Usuario" (add_form)
    # Nota: Django requiere un UserCreationForm personalizado si quitas el username,
    # pero definir add_fieldsets ayuda a organizar los campos extra al crear.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'rol', 'carrera', 'first_name', 'last_name'),
        }),
    )

    # Helpers para mostrar datos relacionados en la tabla
    def get_carrera(self, obj):
        return obj.carrera.nombre if obj.carrera else "-"
    get_carrera.short_description = 'Carrera'

    def get_area(self, obj):
        return obj.carrera.area.nombre if obj.carrera and obj.carrera.area else "-"
    get_area.short_description = 'Área'