from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from inventario.models import Espacio, Recurso

# Validador de peso (Máximo 5MB)
def validate_file_size(value):
    limit = 5 * 1024 * 1024  # 5 MB
    if value.size > limit:
        raise ValidationError('El archivo es muy pesado. El límite es 5MB.')

class Reserva(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'En Revisión'),
        ('APROBADA', 'Aprobada'),
        ('RECHAZADA', 'Rechazada'),
        ('FINALIZADA', 'Finalizada'),
        ('CANCELADA', 'Cancelada'),
    )

    solicitante = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    espacio = models.ForeignKey(Espacio, on_delete=models.PROTECT)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    motivo = models.TextField() # Motivo de la solicitud
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    # NUEVO CAMPO: Motivo de cancelación (Opcional, se llena al cancelar)
    motivo_cancelacion = models.TextField(blank=True, null=True, help_text="Razón por la cual se canceló la reserva")
    
    archivo_adjunto = models.FileField(
        upload_to='reservas_adjuntos/%Y/%m/',
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'xls', 'xlsx']),
            validate_file_size
        ],
        help_text="Solo archivos PDF o Excel. Máx 5MB."
    )

    def clean(self):
        # --- LÓGICA IMPORTANTE ---
        # Si el estado es RECHAZADA o CANCELADA, saltamos la validación de horario.
        # Esto permite rechazar/cancelar aunque haya solapamientos.
        if self.estado in ['RECHAZADA', 'CANCELADA']:
            return

        # Validación básica de nulos
        if not self.hora_inicio or not self.hora_fin:
            return 

        # Validación de NO SOLAPAMIENTO
        # Solo verificamos si chocamos con otras reservas que YA están APROBADAS
        solapamientos = Reserva.objects.filter(
            espacio=self.espacio,
            fecha=self.fecha,
            estado='APROBADA'
        ).exclude(id=self.id)

        for r in solapamientos:
            if self.hora_inicio < r.hora_fin and self.hora_fin > r.hora_inicio:
                raise ValidationError('El espacio ya está ocupado en este horario.')

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva {self.id} - {self.espacio}"

class ReservaRecurso(models.Model):
    reserva = models.ForeignKey(Reserva, related_name='recursos_asociados', on_delete=models.CASCADE)
    recurso = models.ForeignKey(Recurso, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad}x {self.recurso.nombre}"