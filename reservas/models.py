from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from inventario.models import Espacio, Recurso

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

    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="Solicitante"
    )
    espacio = models.ForeignKey(
        Espacio, 
        on_delete=models.PROTECT,
        verbose_name="Espacio Solicitado"
    )
    fecha = models.DateField(verbose_name="Fecha Reserva")
    hora_inicio = models.TimeField(verbose_name="Hora Inicio")
    hora_fin = models.TimeField(verbose_name="Hora Término")
    motivo = models.TextField(verbose_name="Motivo / Actividad")
    
    estado = models.CharField(
        max_length=20, 
        choices=ESTADOS, 
        default='PENDIENTE',
        verbose_name="Estado Actual"
    )
    
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    
    motivo_cancelacion = models.TextField(
        blank=True, 
        null=True, 
        help_text="Razón por la cual se canceló la reserva",
        verbose_name="Motivo Rechazo/Cancelación"
    )
    
    archivo_adjunto = models.FileField(
        upload_to='reservas_adjuntos/%Y/%m/',
        blank=True, 
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'xls', 'xlsx']),
            validate_file_size
        ],
        help_text="Solo archivos PDF o Excel. Máx 5MB.",
        verbose_name="Documento Adjunto"
    )

    # Relación ManyToMany con Recurso a través de la tabla intermedia
    # Esto permite acceder a reserva.recursos.all() si fuera necesario
    recursos = models.ManyToManyField(
        Recurso, 
        through='RecursoReserva', 
        related_name='reservas_involucradas', 
        blank=True
    )

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ['-fecha', '-hora_inicio']


def clean(self):
    # 1) Si se rechaza o cancela, no validamos solapamientos
    if self.estado in ['RECHAZADA', 'CANCELADA']:
        return

    # 2) Validación de campos básicos requeridos para la lógica
    if not self.hora_inicio or not self.hora_fin or not self.fecha:
        return

    # 2.1) Validación lógica del horario
    if self.hora_fin <= self.hora_inicio:
        raise ValidationError("La hora de término debe ser mayor que la hora de inicio.")

    # 3) Verificar si existe el espacio antes de usarlo
    try:
        espacio = self.espacio
    except ObjectDoesNotExist:
        return

    # 3.1) Bloquear reservas nuevas si el espacio está desactivado
    # (no rompe reservas antiguas si luego desactivan el espacio)
    if not self.pk and espacio and not espacio.activo:
        raise ValidationError("Este espacio está desactivado y no se puede reservar.")

    # 4) Validación de NO SOLAPAMIENTO (Básica)
    solapamientos = Reserva.objects.filter(
        espacio=espacio,
        fecha=self.fecha,
        estado='APROBADA'
    ).exclude(id=self.id)

    for r in solapamientos:
        if self.hora_inicio < r.hora_fin and self.hora_fin > r.hora_inicio:
            raise ValidationError("El espacio ya está ocupado (aprobado) en este horario.")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva #{self.id} - {self.espacio} ({self.fecha})"

# ==============================================================================
# MODELO INTERMEDIO (CORREGIDO: RecursoReserva)
# ==============================================================================
class RecursoReserva(models.Model):
    """
    Tabla intermedia para guardar CUÁNTOS recursos de cada tipo se piden.
    Ej: Reserva #5 pide 2 Proyectores.
    """
    reserva = models.ForeignKey(
        Reserva, 
        on_delete=models.CASCADE, 
        related_name='recursos_asociados' # Usado en templates: reserva.recursos_asociados.all
    )
    recurso = models.ForeignKey(
        Recurso, 
        on_delete=models.PROTECT # No permitir borrar recurso si está en una reserva activa
    )
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Recurso en Reserva"
        verbose_name_plural = "Recursos en Reservas"

    def __str__(self):
        return f"{self.cantidad}x {self.recurso.nombre} en Reserva #{self.reserva.id}"