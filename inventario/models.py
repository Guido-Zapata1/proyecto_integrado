from django.db import models

class Espacio(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)
    capacidad = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    
    # NUEVO CAMPO: Imagen del espacio
    imagen = models.ImageField(
        upload_to='espacios/', 
        null=True, 
        blank=True,
        help_text="Foto referencial del espacio"
    )

    def __str__(self):
        return f"{self.nombre} ({self.ubicacion})"

class Recurso(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"

class Recurso(models.Model):
    nombre = models.CharField(max_length=100)
    # CORRECCIÓN: Agregamos 'default=0' para evitar el error de migración
    stock = models.PositiveIntegerField(default=0) 
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"