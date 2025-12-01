from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from .managers import UserManager

# 1. MANAGER PERSONALIZADO
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        """Crea y guarda un usuario con el email y contraseña dados."""
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea y guarda un superusuario con el email y contraseña dados."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'ADMIN')  # Asignamos rol de admin por defecto

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)

# 2. MODELO DE USUARIO
class User(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('SOLICITANTE', 'Solicitante'), # Antes Coordinador
    )

    username = None
    email = models.EmailField(unique=True)

    # Cambiamos el default a SOLICITANTE
    rol = models.CharField(max_length=20, choices=ROLES, default='SOLICITANTE')
    rut = models.CharField(max_length=12, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'rol']

    objects = UserManager() # Asegúrate de que este manager exista/funcione o usa CustomUserManager

    def __str__(self):
        return f"{self.email} ({self.get_rol_display()})"
