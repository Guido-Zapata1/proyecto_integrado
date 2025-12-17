import re
from django.core.exceptions import ValidationError

class ComplexPasswordValidator:
    def validate(self, password, user=None):
        errors = []
        if len(password) < 8:
            errors.append("La contraseña debe tener al menos 8 caracteres.")
        if not re.search(r"[A-Z]", password):
            errors.append("La contraseña debe incluir al menos 1 letra mayúscula.")
        if not re.search(r"[a-z]", password):
            errors.append("La contraseña debe incluir al menos 1 letra minúscula.")
        if not re.search(r"\d", password):
            errors.append("La contraseña debe incluir al menos 1 número.")

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "Debe tener mínimo 8 caracteres e incluir mayúscula, minúscula y número."
