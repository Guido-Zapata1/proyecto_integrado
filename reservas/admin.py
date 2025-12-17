from django.contrib import admin
from .models import Reserva, RecursoReserva

# Configuración para editar los recursos DENTRO de la pantalla de reserva
class RecursoReservaInline(admin.TabularInline):
    model = RecursoReserva
    extra = 1
    # Esto habilita un buscador AJAX para los recursos (requiere search_fields en RecursoAdmin)
    autocomplete_fields = ['recurso'] 
    verbose_name = "Recurso Solicitado"
    verbose_name_plural = "Recursos Solicitados"

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitante', 'espacio', 'fecha', 'hora_inicio', 'hora_fin', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha', 'espacio')
    search_fields = ('solicitante__email', 'solicitante__first_name', 'solicitante__last_name', 'motivo')
    
    # Navegación por fechas en la parte superior
    date_hierarchy = 'fecha'
    
    # Agregamos los recursos como una tabla dentro de la reserva
    inlines = [RecursoReservaInline]

    # Hacemos que la fecha de solicitud sea de solo lectura (es automática)
    readonly_fields = ('fecha_solicitud',)

    # Ordenar por defecto por las más recientes
    ordering = ('-fecha_solicitud',)

@admin.register(RecursoReserva)
class RecursoReservaAdmin(admin.ModelAdmin):
    # Esto permite ver y buscar en la tabla intermedia directamente si fuera necesario
    list_display = ('id', 'reserva', 'recurso', 'cantidad')
    search_fields = ('reserva__id', 'recurso__nombre')
    list_filter = ('recurso',)