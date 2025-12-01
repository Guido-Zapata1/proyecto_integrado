from django.contrib import admin
from .models import Espacio, Recurso

@admin.register(Espacio)
class EspacioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'capacidad', 'ubicacion']

@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'stock', 'descripcion']
