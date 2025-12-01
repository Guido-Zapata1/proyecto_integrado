from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re

class ComplexPasswordValidator:
    """
    Valida que la contraseña contenga caracteres variados:
    - Al menos una mayúscula.
    - Al menos una minúscula.
    - Al menos un número.
    - (Opcional) Al menos un carácter especial.
    """
    
    def validate(self, password, user=None):
        # Verificar Mayúscula
        if not re.search(r'[A-Z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra mayúscula."),
                code='password_no_upper',
            )

        # Verificar Minúscula
        if not re.search(r'[a-z]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos una letra minúscula."),
                code='password_no_lower',
            )

        # Verificar Número
        if not re.search(r'[0-9]', password):
            raise ValidationError(
                _("La contraseña debe contener al menos un número."),
                code='password_no_number',
            )

    def get_help_text(self):
        return _(
            "Tu contraseña debe tener: una mayúscula, una minúscula y un número."
        )