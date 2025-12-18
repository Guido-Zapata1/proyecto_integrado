from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Area, Carrera
from inventario.models import Recurso
from .validators import validate_chilean_rut, normalize_rut

User = get_user_model()

# ==============================================================================
# 1. FORMULARIO DE CREACIÓN DE USUARIO
# ==============================================================================
class CustomUserCreationForm(forms.ModelForm):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Ingrese contraseña"}),
        help_text=(
            "Tu contraseña debe cumplir: mínimo 8 caracteres, no ser común, no ser numérica, "
            "y tener una mayúscula, una minúscula y un número."
        )
    )
    confirm_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Repita la contraseña"})
    )

    rol = forms.ChoiceField(
        label="Rol en el Sistema",
        choices=User.ROLES,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_rol"})
    )

    carrera = forms.ModelChoiceField(
        queryset=Carrera.objects.select_related("area").all(),
        required=True,
        empty_label="-- Selecciona Carrera --",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_carrera"}),
        label="Carrera (Obligatorio)"
    )

    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        disabled=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_area"}),
        label="Área (Automática)"
    )

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "rut", "rol", "tipo_solicitante", "area", "carrera")
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "ejemplo@inacap.cl"}),
            "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombres"}),
            "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Apellidos"}),

            # ✅ evita letras desde el input (igual se valida en backend sí o sí)
            "rut": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Ej: 12.345.678-5",
                "maxlength": "12",
                "inputmode": "text",
                "autocomplete": "off",
                "pattern": r"^[0-9\.]{7,10}-?[0-9kK]{1}$",
                "title": "Formato esperado: 12.345.678-5"
            }),

            "tipo_solicitante": forms.Select(attrs={"class": "form-select"}),
        }

    # -------------------------
    # VALIDACIONES DE UNICIDAD
    # -------------------------
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Debes ingresar un correo.")

        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Este correo ya está registrado.")
        return email

    def clean_rut(self):
        rut_raw = self.cleaned_data.get("rut") or ""
        rut = normalize_rut(rut_raw)
        validate_chilean_rut(rut)

        if User.objects.filter(rut=rut).exists():
            raise ValidationError("Este RUT ya está registrado.")
        return rut

    def clean(self):
        cleaned_data = super().clean()

        # 1) Confirmación de contraseña
        p1 = cleaned_data.get("password")
        p2 = cleaned_data.get("confirm_password")
        if p1 and p2 and p1 != p2:
            self.add_error("confirm_password", "Las contraseñas no coinciden.")

        # 2) Carrera obligatoria
        carrera = cleaned_data.get("carrera")
        if not carrera:
            self.add_error("carrera", "Debes seleccionar una carrera.")

        # 3) Password validators de Django + similitud con datos
        if p1:
            temp_user = User(
                email=cleaned_data.get("email"),
                first_name=cleaned_data.get("first_name"),
                last_name=cleaned_data.get("last_name"),
                rut=cleaned_data.get("rut"),
            )
            try:
                validate_password(p1, user=temp_user)
            except ValidationError as e:
                self.add_error("password", e)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = (self.cleaned_data.get("email") or "").strip().lower()
        user.rut = self.cleaned_data.get("rut")  # ya viene normalizado

        user.set_password(self.cleaned_data["password"])

        carrera = self.cleaned_data.get("carrera")
        if carrera:
            user.carrera = carrera
            user.area = carrera.area

        if commit:
            user.save()
        return user


# ==============================================================================
# 2. FORMULARIO DE EDICIÓN DE USUARIO
# ==============================================================================
class EditarUsuarioForm(forms.ModelForm):
    area_filtro = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        label="Área / Facultad (Filtro)",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_area_filtro"})
    )

    carrera = forms.ModelChoiceField(
        queryset=Carrera.objects.select_related("area").all(),
        required=True,
        empty_label="-- Selecciona Carrera --",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_carrera_edit"}),
        label="Carrera (Obligatorio)"
    )

    area = forms.ModelChoiceField(
        queryset=Area.objects.all(),
        required=False,
        disabled=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "id_area_docente"}),
        label="Área (Automática)"
    )

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "rut", "rol", "tipo_solicitante", "area", "carrera"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),

            "email": forms.EmailInput(attrs={"class": "form-control"}),

            "rut": forms.TextInput(attrs={
                "class": "form-control",
                "maxlength": "12",
                "autocomplete": "off",
                "pattern": r"^[0-9\.]{7,10}-?[0-9kK]{1}$",
                "title": "Formato esperado: 12.345.678-5"
            }),

            "rol": forms.Select(attrs={"class": "form-select", "id": "id_rol"}),
            "tipo_solicitante": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk and getattr(self.instance, "carrera", None):
            self.fields["area"].initial = self.instance.carrera.area
            self.fields["area_filtro"].initial = self.instance.carrera.area
        elif self.instance.pk and getattr(self.instance, "area", None):
            self.fields["area"].initial = self.instance.area
            self.fields["area_filtro"].initial = self.instance.area

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if not email:
            raise ValidationError("Debes ingresar un correo.")

        qs = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Este correo ya está registrado.")
        return email

    def clean_rut(self):
        rut_raw = self.cleaned_data.get("rut") or ""
        rut = normalize_rut(rut_raw)
        validate_chilean_rut(rut)

        qs = User.objects.filter(rut=rut).exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Este RUT ya está registrado.")
        return rut

    def clean(self):
        cleaned_data = super().clean()
        carrera = cleaned_data.get("carrera")
        if not carrera:
            self.add_error("carrera", "Debes seleccionar una carrera.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = (self.cleaned_data.get("email") or "").strip().lower()
        user.rut = self.cleaned_data.get("rut")  # normalizado

        carrera = self.cleaned_data.get("carrera")
        if carrera:
            user.carrera = carrera
            user.area = carrera.area

        if commit:
            user.save()
        return user


# ==============================================================================
# 3. FORMULARIO PARA ÁREAS
# ==============================================================================
class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ["nombre", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Ingeniería, Salud..."}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción opcional"}),
        }


# ==============================================================================
# 4. FORMULARIO PARA CARRERAS
# ==============================================================================
class CarreraForm(forms.ModelForm):
    class Meta:
        model = Carrera
        fields = ["area", "nombre", "codigo"]
        widgets = {
            "area": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Ingeniería en Informática"}),
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: IINF-001"}),
        }


# ==============================================================================
# 5. FORMULARIO PARA RECURSOS (INVENTARIO)
# ==============================================================================
class RecursoForm(forms.ModelForm):
    class Meta:
        model = Recurso
        fields = ["codigo", "nombre", "stock", "descripcion"]
        widgets = {
            "codigo": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: PROY-001"}),
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: Proyector Sony"}),
            "stock": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
