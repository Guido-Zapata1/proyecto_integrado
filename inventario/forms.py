from django import forms
from .models import Espacio, Recurso

class EspacioForm(forms.ModelForm):
    class Meta:
        model = Espacio
        fields = "__all__"


class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recurso
        fields = "__all__"
