from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse

from .models import Notificacion


@login_required
def lista(request):
    notifs = Notificacion.objects.filter(usuario=request.user)[:100]
    return render(request, "notificaciones/lista.html", {"notifs": notifs})


@login_required
def marcar_leida(request, pk):
    n = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    n.leida = True
    n.save(update_fields=["leida"])
    if n.url:
        return redirect(n.url)
    return redirect("notificaciones:lista")


@login_required
def marcar_todas_leidas(request):
    Notificacion.objects.filter(usuario=request.user, leida=False).update(leida=True)
    return redirect("notificaciones:lista")


@login_required
def unread_count(request):
    c = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    return JsonResponse({"unread": c})
