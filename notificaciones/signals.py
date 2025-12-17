from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse
from django.apps import apps

from .utils import notificar, notificar_muchos


def _get_user_model():
    # Si tu user está en otra app/model, aquí se ajusta.
    return apps.get_model("core", "User")


def _admins_qs():
    User = _get_user_model()
    # Admins por rol (y activos)
    return User.objects.filter(rol="ADMIN", is_active=True)


def _gestion_solicitudes_url():
    try:
        return reverse("gestion_reservas")
    except Exception:
        return ""


def _reserva_detalle_url(reserva):
    try:
        return reverse("reservas:detalle_reserva", args=[reserva.id])
    except Exception:
        return ""


# =============================================================================
# 1) NOTIFICAR A ADMINS CUANDO SE CREA UNA RESERVA (NUEVA SOLICITUD)
# =============================================================================
@receiver(post_save, sender=apps.get_model("reservas", "Reserva"))
def notif_admin_reserva_creada(sender, instance, created, **kwargs):
    if not created:
        return

    titulo = "Nueva solicitud de reserva"
    mensaje = (
        f"{instance.solicitante} solicitó {instance.espacio} "
        f"para {instance.fecha} ({instance.hora_inicio}-{instance.hora_fin})."
    )

    # ✅ click => Gestión Solicitudes
    url = _gestion_solicitudes_url()

    notificar_muchos(_admins_qs(), titulo, mensaje, level="INFO", url=url)


# =============================================================================
# 2) NOTIFICAR AL USUARIO CUANDO CAMBIA EL ESTADO DE SU RESERVA
#    (APROBADA / RECHAZADA / CANCELADA / etc.)
# =============================================================================
@receiver(pre_save, sender=apps.get_model("reservas", "Reserva"))
def notif_usuario_cambio_estado(sender, instance, **kwargs):
    # Si aún no existe en DB, no hay "estado anterior"
    if not instance.pk:
        return

    Reserva = apps.get_model("reservas", "Reserva")
    old = Reserva.objects.filter(pk=instance.pk).only("estado", "motivo_cancelacion").first()
    if not old:
        return

    if old.estado == instance.estado:
        return

    titulo = "Actualización de tu reserva"

    # Mensajes en español
    if instance.estado == "APROBADA":
        mensaje = f"Tu reserva para {instance.espacio} el {instance.fecha} fue APROBADA."
        level = "SUCCESS"
    elif instance.estado == "RECHAZADA":
        extra = ""
        # si existe motivo_cancelacion o similar, lo agregamos
        if getattr(instance, "motivo_cancelacion", None):
            extra = f" Motivo: {instance.motivo_cancelacion}"
        mensaje = f"Tu reserva para {instance.espacio} el {instance.fecha} fue RECHAZADA.{extra}"
        level = "DANGER"
    elif instance.estado == "CANCELADA":
        extra = ""
        if getattr(instance, "motivo_cancelacion", None):
            extra = f" Motivo: {instance.motivo_cancelacion}"
        mensaje = f"Tu reserva para {instance.espacio} el {instance.fecha} fue CANCELADA.{extra}"
        level = "WARNING"
    else:
        mensaje = (
            f"Tu reserva para {instance.espacio} el {instance.fecha} cambió a: {instance.estado}."
        )
        level = "INFO"

    # ✅ Para el usuario conviene ir al detalle de su reserva
    url = _reserva_detalle_url(instance)

    # Notificar al solicitante
    if getattr(instance, "solicitante_id", None):
        notificar(instance.solicitante, titulo, mensaje, level=level, url=url)


# =============================================================================
# 3) NOTIFICAR CUANDO SE DESACTIVA UN ESPACIO
# =============================================================================
@receiver(pre_save, sender=apps.get_model("inventario", "Espacio"))
def notif_espacio_desactivado(sender, instance, **kwargs):
    if not instance.pk:
        return

    Espacio = apps.get_model("inventario", "Espacio")
    old = Espacio.objects.filter(pk=instance.pk).only("activo", "nombre").first()
    if not old:
        return

    # Si se desactiva (True -> False)
    if old.activo and (instance.activo is False):
        Reserva = apps.get_model("reservas", "Reserva")

        hoy = timezone.localdate()
        reservas_afectadas = Reserva.objects.filter(
            espacio=instance,
            fecha__gte=hoy,
            estado__in=["PENDIENTE", "APROBADA"],
        ).select_related("solicitante")

        usuarios = {r.solicitante for r in reservas_afectadas if getattr(r, "solicitante_id", None)}
        if usuarios:
            titulo = "Espacio desactivado"
            mensaje = (
                f"El espacio '{instance.nombre}' fue desactivado. "
                f"Si tenías reservas próximas, revisa tu historial."
            )
            notificar_muchos(usuarios, titulo, mensaje, level="WARNING")
