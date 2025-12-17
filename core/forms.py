from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import Area, Carrera
from inventario.models import Recurso

User = get_user_model()

# ==============================================================================
# 1. FORMULARIO DE CREACIÓN DE USUARIO
# ==============================================================================
class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese contraseña'})
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repita la contraseña'})
    )

    rol = forms.ChoiceField(
        label="Rol en el Sistema",
        choices=User.ROLES,
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_rol'})
    )

    # Campo para seleccionar Carrera (Opcional, se oculta para Docentes)
    carrera = forms.ModelChoiceField(
        queryset=Carrera.objects.all(),
        required=False,
        empty_label="-- Sin Carrera --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Carrera"
    )

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'rut', 'rol', 'tipo_solicitante', 'area', 'carrera')

        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'ejemplo@inacap.cl'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombres'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellidos'}),
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 12.345.678-9'}),
            'tipo_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error('confirm_password', "Las contraseñas no coinciden")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

# ==============================================================================
# 2. FORMULARIO DE EDICIÓN DE USUARIO
# ==============================================================================
class EditarUsuarioForm(forms.ModelForm):
    # Campo auxiliar para filtrar carreras/áreas en el frontend si es necesario
    area_filtro = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        label="Área / Facultad",
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_area_filtro'})
    )

    class Meta:
        model = User
        # Incluimos 'area' directamente para guardarlo en la vista
        fields = ['first_name', 'last_name', 'email', 'rut', 'rol', 'tipo_solicitante', 'area'] 
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'rut': forms.TextInput(attrs={'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select', 'id': 'id_rol'}),
            'tipo_solicitante': forms.Select(attrs={'class': 'form-select'}),
            'area': forms.Select(attrs={'class': 'form-select', 'id': 'id_area_docente'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Si el usuario ya tiene un área asignada, inicializamos el filtro con ella
        if self.instance.pk and self.instance.area:
            self.fields['area_filtro'].initial = self.instance.area

# ==============================================================================
# 3. FORMULARIO PARA ÁREAS
# ==============================================================================
class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['nombre', 'descripcion']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ingeniería, Salud...'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción opcional'}),
        }

# ==============================================================================
# 4. FORMULARIO PARA CARRERAS
# ==============================================================================
class CarreraForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = ['area', 'nombre', 'codigo']
        widgets = {
            'area': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Ingeniería en Informática'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: IINF-001'}),
        }

# ==============================================================================
# 5. FORMULARIO PARA RECURSOS (INVENTARIO)
# ==============================================================================
class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recurso
        fields = ['codigo', 'nombre', 'stock', 'descripcion']
        widgets = {
            'codigo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: PROY-001'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Proyector Sony'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }