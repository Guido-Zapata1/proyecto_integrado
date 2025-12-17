from django.contrib import admin
from .models import Espacio, Recurso

@admin.register(Espacio)
class EspacioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'ubicacion', 'activo')
    search_fields = ('nombre', 'ubicacion')
    list_filter = ('activo',)

@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    # Mostramos el nombre, código, stock total y el stock disponible calculado
    list_display = ('nombre', 'codigo', 'stock', 'stock_disponible_admin')
    
    # --- IMPORTANTE: ESTA LÍNEA SOLUCIONA EL ERROR admin.E040 ---
    # Define por qué campos se buscará cuando uses el autocompletar en Reservas
    search_fields = ('nombre', 'codigo') 
    # -----------------------------------------------------------

    # Helper para mostrar la propiedad @property del modelo en el admin
    def stock_disponible_admin(self, obj):
        return obj.stock_disponible
    stock_disponible_admin.short_description = 'Disponible (Real)'