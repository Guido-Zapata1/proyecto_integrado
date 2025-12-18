import re
from django.core.exceptions import ValidationError

# =========================
# RUT (Chile)
# =========================
def normalize_rut(value: str) -> str:
    """
    Normaliza el RUT a formato: 12345678-5 (sin puntos, DV en mayúscula).
    Acepta: 9.736.809-0 o 9736809-0 o 97368090
    """
    if value is None:
        return ""

    rut = str(value).strip().upper()
    rut = rut.replace(".", "").replace(" ", "")

    # Permite formatos: 12345678-9 o 123456789 (sin guion)
    if "-" not in rut and len(rut) >= 2:
        rut = rut[:-1] + "-" + rut[-1]

    return rut


def _calc_dv(rut_num: str) -> str:
    """
    Calcula el DV del RUT (módulo 11).
    """
    suma = 0
    multiplo = 2

    for c in reversed(rut_num):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1

    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def validate_chilean_rut(value: str):
    """
    Valida:
    - Solo números + DV (K permitido)
    - DV correcto
    """
    rut = normalize_rut(value)

    if not rut:
        raise ValidationError("Debes ingresar un RUT.")

    # 12345678-5
    if not re.fullmatch(r"\d{7,8}-[\dK]", rut):
        raise ValidationError("RUT inválido. Formato esperado: 12.345.678-5")

    rut_num, dv = rut.split("-")
    dv_calc = _calc_dv(rut_num)

    if dv != dv_calc:
        raise ValidationError("RUT inválido. Dígito verificador incorrecto.")


# =========================
# PASSWORD VALIDATORS
# =========================
class ComplexPasswordValidator:
    """
    Exige:
    - mínimo 8
    - al menos 1 mayúscula, 1 minúscula, 1 número
    """
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("La contraseña es demasiado corta. Debe contener por lo menos 8 caracteres.")

        if not re.search(r"[A-Z]", password):
            raise ValidationError("Tu contraseña debe tener al menos una mayúscula.")

        if not re.search(r"[a-z]", password):
            raise ValidationError("Tu contraseña debe tener al menos una minúscula.")

        if not re.search(r"\d", password):
            raise ValidationError("Tu contraseña debe tener al menos un número.")

    def get_help_text(self):
        return "Debe tener al menos 8 caracteres, una mayúscula, una minúscula y un número."


class NotSameAsOldPasswordValidator:
    """
    Evita que el usuario cambie la contraseña por la misma que ya tenía.
    (Aplica en password_change y también si usas validate_password en creación)
    """
    def validate(self, password, user=None):
        if user and user.pk and user.has_usable_password():
            if user.check_password(password):
                raise ValidationError("La nueva contraseña no puede ser igual a la contraseña actual.")

    def get_help_text(self):
        return "La nueva contraseña no puede ser igual a la contraseña actual."
