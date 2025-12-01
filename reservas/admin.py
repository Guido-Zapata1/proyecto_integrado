from django.contrib import admin
from .models import Reserva, ReservaRecurso

# Esto permite agregar recursos dentro de la misma pantalla de la reserva (Inline)
class ReservaRecursoInline(admin.TabularInline):
    model = ReservaRecurso
    extra = 1

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('id', 'solicitante', 'espacio', 'fecha', 'hora_inicio', 'hora_fin', 'estado')
    list_filter = ('estado', 'fecha', 'espacio')
    search_fields = ('solicitante__email', 'motivo')
    list_editable = ('estado',) # ¡Truco Pro! Permite cambiar el estado directo desde la lista
    inlines = [ReservaRecursoInline]