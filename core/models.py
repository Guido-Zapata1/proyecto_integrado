from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.apps import apps

# ==============================================================================
# 1. MANAGER PERSONALIZADO
# ==============================================================================
class CustomUserManager(BaseUserManager):
    def _get_default_carrera(self):
        """
        Crea/obtiene una Carrera por defecto para que ningún usuario quede sin carrera.
        Evita que createsuperuser o scripts revienten si no mandan carrera.
        """
        Area = apps.get_model("core", "Area")
        Carrera = apps.get_model("core", "Carrera")

        area_default, _ = Area.objects.get_or_create(
            nombre="SIN ÁREA",
            defaults={"descripcion": "Área por defecto para usuarios sin asignación."},
        )
        carrera_default, _ = Carrera.objects.get_or_create(
            nombre="SIN CARRERA",
            defaults={"area": area_default, "codigo": "SIN"},
        )
        return carrera_default

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")

        email = self.normalize_email(email)

        # ✅ Forzar que siempre tenga carrera (si no llega, asigna la default)
        if not extra_fields.get("carrera"):
            extra_fields["carrera"] = self._get_default_carrera()

        # ✅ Sincroniza área desde carrera (para no romper tu código viejo)
        if extra_fields.get("carrera"):
            extra_fields["area"] = extra_fields["carrera"].area

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("rol", "ADMIN")

        # ✅ Si superuser no trae carrera, poner default para no romper
        if not extra_fields.get("carrera"):
            extra_fields["carrera"] = self._get_default_carrera()

        # ✅ Sincroniza área desde carrera
        extra_fields["area"] = extra_fields["carrera"].area

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


# ==============================================================================
# 2. MODELOS DE ORGANIZACIÓN (Áreas y Carreras)
# ==============================================================================
class Area(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Área")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Área"
        verbose_name_plural = "Áreas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Carrera(models.Model):
    area = models.ForeignKey(
        Area,
        on_delete=models.CASCADE,
        related_name="carreras",
        verbose_name="Área Perteneciente",
    )
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Carrera")
    codigo = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código Interno")

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"


# ==============================================================================
# 3. MODELO DE USUARIO
# ==============================================================================
class User(AbstractUser):
    # ROLES DEL SISTEMA
    ROLES = (
        ("ADMIN", "Administrador"),
        ("SOLICITANTE", "Solicitante"),
    )

    # TIPOS SOLICITANTE
    TIPOS_SOLICITANTE = (
        ("DOCENTE", "Docente"),
        ("COORDINADOR", "Coordinador"),
        ("AMBOS", "Docente y Coordinador"),
    )

    username = None
    email = models.EmailField(unique=True, verbose_name="Correo Electrónico")

    rol = models.CharField(max_length=20, choices=ROLES, default="SOLICITANTE", verbose_name="Rol de Sistema")

    tipo_solicitante = models.CharField(
        max_length=20,
        choices=TIPOS_SOLICITANTE,
        default="DOCENTE",
        verbose_name="Tipo de Usuario",
    )

    rut = models.CharField(max_length=12, blank=True, null=True, verbose_name="RUT")

    # ✅ Mantenemos 'area' para no romper nada (templates/vistas), pero se auto-sync desde carrera
    area = models.ForeignKey(
        Area,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usuarios_directos",
        verbose_name="Área (Facultad)",
    )

    # ✅ AHORA: todos deben tener carrera (a nivel de aplicación + manager)
    # Para NO romper la BD de una (si tienes usuarios antiguos sin carrera),
    # la dejamos nullable por ahora, pero la lógica evita que quede nula.
    carrera = models.ForeignKey(
        Carrera,
        on_delete=models.PROTECT,  # más seguro que SET_NULL si quieres exigir carrera
        null=True,                 # <- así NO se rompe tu migrate si ya hay usuarios sin carrera
        blank=True,                # <- igual
        related_name="usuarios",
        verbose_name="Carrera",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "rol"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        cargo = self.get_tipo_solicitante_display() if self.rol == "SOLICITANTE" else "Admin"
        return f"{self.email} ({cargo})"

    def save(self, *args, **kwargs):
        # ✅ Si tiene carrera, el área SIEMPRE se calcula desde carrera.area
        if self.carrera_id and self.carrera and self.carrera.area_id:
            self.area = self.carrera.area
        super().save(*args, **kwargs)

    @property
    def nombre_area(self):
        # 1) área desde carrera (nuevo)
        if self.carrera and self.carrera.area:
            return self.carrera.area.nombre
        # 2) fallback compatibilidad (viejo)
        if self.area:
            return self.area.nombre
        return "Sin Área"
