from django.db import models
from django.db.models import Sum

class Espacio(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=200)
    capacidad = models.PositiveIntegerField()
    activo = models.BooleanField(default=True)
    
    # Campo para imagen del espacio (requiere configuración de MEDIA en settings.py)
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
    
    # Campo código único para inventario (Ya con unique=True activado)
    codigo = models.CharField(
        max_length=50, 
        #unique=True, 
        verbose_name="Código Interno", 
        default="SIN-COD"
    )
    
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock Total Físico")
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock})"

    @property
    def stock_disponible(self):
        """
        Calcula el stock real disponible para nuevas reservas.
        Fórmula: Stock Total - (Cantidad en Reservas PENDIENTES + APROBADAS)
        """
        # Importamos aquí dentro para evitar errores de "Importación Circular" con la app reservas
        try:
            from reservas.models import RecursoReserva 
            
            # Sumamos la cantidad de este recurso comprometida en reservas activas
            ocupados = RecursoReserva.objects.filter(
                recurso=self,
                reserva__estado__in=['PENDIENTE', 'APROBADA']
            ).aggregate(total=Sum('cantidad'))['total'] or 0
            
            disponible = self.stock - ocupados
            return max(disponible, 0) # Aseguramos que nunca devuelva negativo
        except ImportError:
            # Si el modelo de reservas aún no existe (ej: durante migraciones iniciales), devolvemos el total
            return self.stock