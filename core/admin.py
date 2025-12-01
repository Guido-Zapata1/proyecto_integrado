from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from django.forms import ModelForm

class CustomUserCreationForm(ModelForm):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'rol')

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = User

    list_display = ("email", "first_name", "last_name", "rol", "is_active", "is_staff")
    list_filter = ("rol", "is_active", "is_staff")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Información Personal", {"fields": ("first_name", "last_name", "rut")}),
        ("Permisos", {"fields": ("rol", "is_active", "is_staff", "is_superuser")}),
        ("Fechas", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "first_name", "last_name", "rol"),
        }),
    )

    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")

admin.site.register(User, CustomUserAdmin)

