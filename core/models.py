from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# ==============================================================================
# 1. MANAGER PERSONALIZADO
# ==============================================================================
class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('rol', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser debe tener is_superuser=True.')

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
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Carrera(models.Model):
    area = models.ForeignKey(
        Area, 
        on_delete=models.CASCADE, 
        related_name='carreras',
        verbose_name="Área Perteneciente"
    )
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Carrera")
    codigo = models.CharField(max_length=20, blank=True, null=True, verbose_name="Código Interno")

    class Meta:
        verbose_name = "Carrera"
        verbose_name_plural = "Carreras"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.area.nombre})"

# ==============================================================================
# 3. MODELO DE USUARIO (Actualizado con Sub-Roles)
# ==============================================================================
class User(AbstractUser):
    # ROLES DEL SISTEMA (Permisos Globales)
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('SOLICITANTE', 'Solicitante'), 
    )

    # SUB-ROLES O CARGOS (Solo aplica si es SOLICITANTE)
    # Se eliminó ALUMNO por solicitud
    TIPOS_SOLICITANTE = (
        ('DOCENTE', 'Docente'),                 # Vinculado a Área
        ('COORDINADOR', 'Coordinador'),         # Vinculado a Área
        ('AMBOS', 'Docente y Coordinador'),     # Vinculado a Área
    )

    username = None
    email = models.EmailField(unique=True, verbose_name='Correo Electrónico')

    # Rol Principal (Define acceso al panel admin vs sitio normal)
    rol = models.CharField(max_length=20, choices=ROLES, default='SOLICITANTE', verbose_name="Rol de Sistema")
    
    # Nuevo: Cargo específico dentro de la institución
    tipo_solicitante = models.CharField(
        max_length=20, 
        choices=TIPOS_SOLICITANTE, 
        default='DOCENTE',  # Cambiado default de ALUMNO a DOCENTE
        verbose_name="Tipo de Usuario"
    )
    
    rut = models.CharField(max_length=12, blank=True, null=True, verbose_name="RUT")

    # Vinculación Directa a Área (Para Docentes/Coordinadores que no tienen carrera)
    area = models.ForeignKey(
        Area, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='usuarios_directos',
        verbose_name="Área (Facultad)"
    )

    # Vinculación a Carrera (Mantenida por compatibilidad si vuelve alumno, opcional)
    carrera = models.ForeignKey(
        Carrera, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='usuarios',
        verbose_name="Carrera"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'rol']

    objects = CustomUserManager()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        cargo = self.get_tipo_solicitante_display() if self.rol == 'SOLICITANTE' else 'Admin'
        return f"{self.email} ({cargo})"
    
    @property
    def nombre_area(self):
        # Lógica inteligente para saber el área del usuario
        # 1. Si tiene carrera asignada (caso legacy o futuro alumno), el área es la de su carrera.
        if self.carrera and self.carrera.area:
            return self.carrera.area.nombre
        # 2. Si es Docente/Coordinador, usa su área directa.
        if self.area:
            return self.area.nombre
        return "Sin Área"