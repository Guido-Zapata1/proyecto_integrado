from django import forms
from django.utils import timezone
from datetime import datetime, timedelta, date
from .models import Reserva

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['espacio', 'fecha', 'hora_inicio', 'hora_fin', 'motivo', 'archivo_adjunto']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'espacio': forms.Select(attrs={'class': 'form-select'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'archivo_adjunto': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.xls,.xlsx'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')

        # 1. Validación: Hora Fin > Hora Inicio
        if hora_inicio and hora_fin:
            if hora_fin <= hora_inicio:
                self.add_error('hora_fin', "La hora de término debe ser posterior a la de inicio.")

        # 2. Validación de Negocio: 24 Horas de Anticipación
        if fecha and hora_inicio:
            try:
                # Combinamos fecha y hora y asignamos zona horaria para comparar correctamente con "ahora"
                reserva_dt = datetime.combine(fecha, hora_inicio)
                reserva_dt = timezone.make_aware(reserva_dt, timezone.get_current_timezone())
                
                ahora = timezone.localtime(timezone.now())
                limite_minimo = ahora + timedelta(hours=24)
                
                if reserva_dt < limite_minimo:
                    self.add_error('fecha', f"Anticipación insuficiente. Debes reservar para después del {limite_minimo.strftime('%d/%m %H:%M')} (24h mín).")
            except Exception:
                # Si hay error en formato de fecha, Django ya lanzará su propio error de campo
                pass

        # 3. Validación de Negocio: Duración Máxima (4 Horas)
        if hora_inicio and hora_fin:
            # Usamos fecha dummy para restar solo horas sin que importe el día
            dummy_date = date(2000, 1, 1)
            dt_inicio = datetime.combine(dummy_date, hora_inicio)
            dt_fin = datetime.combine(dummy_date, hora_fin)
            
            # Solo validamos duración si el fin es lógicamente mayor al inicio
            if dt_fin > dt_inicio:
                duracion = dt_fin - dt_inicio
                if duracion.total_seconds() > (4 * 3600): # 4 horas en segundos
                    self.add_error('hora_fin', "La duración máxima permitida es de 4 horas.")

        return cleaned_data
            