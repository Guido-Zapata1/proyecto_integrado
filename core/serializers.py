from rest_framework import serializers
from .models import User, Area, Carrera

# 1. Serializer para Áreas
class AreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Area
        fields = ['id', 'nombre', 'descripcion']

# 2. Serializer para Carreras
class CarreraSerializer(serializers.ModelSerializer):
    # Campo extra para mostrar el nombre del área en el frontend sin hacer otra petición
    nombre_area = serializers.ReadOnlyField(source='area.nombre')

    class Meta:
        model = Carrera
        fields = ['id', 'nombre', 'codigo', 'area', 'nombre_area']

# 3. Serializer para Usuarios
class UserSerializer(serializers.ModelSerializer):
    # Mostramos nombres legibles además de los IDs
    nombre_carrera = serializers.ReadOnlyField(source='carrera.nombre')
    nombre_area = serializers.ReadOnlyField(source='nombre_area') # Usa la propiedad @property del modelo

    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 
            'rol', 'rut', 'carrera', 'nombre_carrera', 'nombre_area'
        ]