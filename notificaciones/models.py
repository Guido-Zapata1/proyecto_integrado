from django.conf import settings
from django.db import models


class Notificacion(models.Model):
    LEVELS = (
        ("INFO", "Info"),
        ("SUCCESS", "Success"),
        ("WARNING", "Warning"),
        ("DANGER", "Danger"),
    )

    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notificaciones")
    titulo = models.CharField(max_length=120)
    mensaje = models.TextField()
    level = models.CharField(max_length=10, choices=LEVELS, default="INFO")
    url = models.CharField(max_length=300, blank=True, default="")
    leida = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creada_en"]

    def __str__(self):
        return f"{self.usuario} - {self.titulo}"
