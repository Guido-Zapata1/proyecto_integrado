from django import forms
from django.core.exceptions import ValidationError
from datetime import timedelta, datetime, time
from .models import Reserva
from inventario.models import Espacio

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['espacio', 'fecha', 'hora_inicio', 'hora_fin', 'motivo', 'archivo_adjunto']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'id': 'id_fecha'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'id_hora_inicio'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control', 'id': 'id_hora_fin'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describa el motivo de la reserva...'}),
            'espacio': forms.Select(attrs={'class': 'form-select', 'id': 'id_espacio'}),
            'archivo_adjunto': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['espacio'].queryset = Espacio.objects.filter(activo=True).order_by('nombre')
        self.fields['archivo_adjunto'].required = False

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        espacio = cleaned_data.get('espacio')

        if not (fecha and hora_inicio and hora_fin and espacio):
            return

        # ==============================================================================
        # 0. REGLA: Anticipación Mínima de 48 Horas
        # ==============================================================================
        # Combinamos fecha y hora para tener el momento exacto de inicio
        inicio_reserva = datetime.combine(fecha, hora_inicio)
        ahora = datetime.now()

        # Calculamos la diferencia
        tiempo_anticipacion = inicio_reserva - ahora

        if tiempo_anticipacion < timedelta(hours=48):
            raise ValidationError("Debe realizar la solicitud con al menos 48 horas de anticipación.")

        # ==============================================================================
        # 1. REGLA: Horario permitido (08:30 AM a 21:00 PM)
        # ==============================================================================
        inicio_permitido = time(8, 30)
        fin_permitido = time(21, 0)

        if hora_inicio < inicio_permitido or hora_fin > fin_permitido:
            raise ValidationError("El horario de funcionamiento es estrictamente de 08:30 a 21:00 hrs.")
        
        if hora_fin <= hora_inicio:
            self.add_error('hora_fin', "La hora de término debe ser posterior a la de inicio.")
            return

        # ==============================================================================
        # 2. REGLA: Duración mínima de 1 hora
        # ==============================================================================
        dummy_date = datetime.today()
        dt_inicio = datetime.combine(dummy_date, hora_inicio)
        dt_fin = datetime.combine(dummy_date, hora_fin)
        
        duracion = dt_fin - dt_inicio
        if duracion < timedelta(hours=1):
            raise ValidationError("La reserva debe tener una duración mínima de 1 hora.")

        # ==============================================================================
        # 3. REGLA: Colchón de 1 hora entre reservas (Buffer)
        # ==============================================================================
        margen = timedelta(hours=1)
        mi_inicio_real = datetime.combine(fecha, hora_inicio)
        mi_fin_real = datetime.combine(fecha, hora_fin)
        
        rango_inicio_seguro = (mi_inicio_real - margen).time()
        rango_fin_seguro = (mi_fin_real + margen).time()

        reservas_conflicto = Reserva.objects.filter(
            espacio=espacio,
            fecha=fecha,
            estado__in=['APROBADA', 'PENDIENTE']
        ).exclude(pk=self.instance.pk)

        for r in reservas_conflicto:
            if r.hora_inicio < rango_fin_seguro and r.hora_fin > rango_inicio_seguro:
                raise ValidationError(
                    f"Conflicto de horario o margen de espera insuficiente. "
                    f"Existe una reserva ocupando el bloque {r.hora_inicio} - {r.hora_fin}. "
                    f"Recuerda que debe haber 1 hora de diferencia entre reservas."
                )

        return cleaned_data