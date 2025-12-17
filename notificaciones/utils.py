from .models import Notificacion


def notificar(usuario, titulo, mensaje, level="INFO", url=""):
    Notificacion.objects.create(
        usuario=usuario,
        titulo=titulo,
        mensaje=mensaje,
        level=level,
        url=url or "",
    )


def notificar_muchos(qs_usuarios, titulo, mensaje, level="INFO", url=""):
    # qs_usuarios: QuerySet de usuarios
    objs = [
        Notificacion(usuario=u, titulo=titulo, mensaje=mensaje, level=level, url=url or "")
        for u in qs_usuarios
    ]
    Notificacion.objects.bulk_create(objs)
