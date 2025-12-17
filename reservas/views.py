import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.core.exceptions import ValidationError

from .forms import ReservaForm
from .models import Reserva, RecursoReserva
from inventario.models import Recurso, Espacio


@login_required
def listar_reservas(request):
    estado_filter = request.GET.get('estado', 'TODAS')
    qs = Reserva.objects.filter(solicitante=request.user).order_by('-fecha', '-hora_inicio')

    if estado_filter != 'TODAS':
        qs = qs.filter(estado=estado_filter)

    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'reservas/listar_reservas.html', {
        'reservas': page_obj.object_list,
        'page_obj': page_obj,
    })


@login_required
def crear_reserva(request):
    recursos_disponibles = Recurso.objects.filter(stock__gt=0)
    espacios_activos = Espacio.objects.filter(activo=True)

    recursos_iniciales_json = "[]"

    if request.method == 'POST':
        form = ReservaForm(request.POST, request.FILES)

        recursos_a_pedir = []
        for key, value in request.POST.items():
            if key.startswith('recurso_'):
                try:
                    recurso_id = int(key.split('_')[1])
                    cantidad = int(value)
                    if cantidad > 0:
                        recursos_a_pedir.append({'id': recurso_id, 'cantidad': cantidad})
                except ValueError:
                    continue

        # ✅ Para repoblar carrito si hay error
        if recursos_a_pedir:
            ids = [x["id"] for x in recursos_a_pedir]
            recursos_db = {r.id: r.nombre for r in Recurso.objects.filter(id__in=ids)}
            recursos_asignados = []
            for item in recursos_a_pedir:
                rid = item["id"]
                recursos_asignados.append({
                    "id": str(rid),
                    "nombre": recursos_db.get(rid, f"Recurso #{rid}"),
                    "cantidad": item["cantidad"],
                })
            recursos_iniciales_json = json.dumps(recursos_asignados)

        if form.is_valid():
            try:
                with transaction.atomic():
                    reserva = form.save(commit=False)
                    reserva.solicitante = request.user
                    reserva.save()

                    for item in recursos_a_pedir:
                        recurso_db = Recurso.objects.select_for_update().get(id=item['id'])
                        cantidad_pedida = item['cantidad']

                        ocupados = RecursoReserva.objects.filter(
                            recurso=recurso_db,
                            reserva__estado__in=['PENDIENTE', 'APROBADA'],
                            reserva__fecha=reserva.fecha
                        ).filter(
                            Q(reserva__hora_inicio__lt=reserva.hora_fin) &
                            Q(reserva__hora_fin__gt=reserva.hora_inicio)
                        ).aggregate(total=Sum('cantidad'))['total'] or 0

                        disponible_real = recurso_db.stock - ocupados

                        if disponible_real < cantidad_pedida:
                            raise ValueError(
                                f"Stock insuficiente para {recurso_db.nombre}. "
                                f"Disponible: {disponible_real}, Pedido: {cantidad_pedida}"
                            )

                        RecursoReserva.objects.create(
                            reserva=reserva,
                            recurso=recurso_db,
                            cantidad=cantidad_pedida
                        )

                    messages.success(request, 'Solicitud creada con éxito. Esperando aprobación.')
                    return redirect('reservas:listar_reservas')

            except Exception as e:
                messages.error(request, f"Error al procesar la reserva: {e}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = ReservaForm()

    context = {
        'form': form,
        'recursos_disponibles': recursos_disponibles,
        'espacios': espacios_activos,
        'recursos_iniciales': recursos_iniciales_json,  # ✅ mantiene carrito tras error
    }
    return render(request, 'reservas/crear_reserva.html', context)


@login_required
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(
        Reserva.objects.prefetch_related('recursos_asociados__recurso'),
        pk=reserva_id,
        solicitante=request.user
    )
    return render(request, 'reservas/detalle_reserva.html', {'reserva': reserva})


@login_required
def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, solicititante=request.user)  # ⚠️ si te da error, vuelve a solicitante
    # (Si tu archivo real ya estaba bien, deja solicitante=request.user como lo tenías)


@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, solicitante=request.user)
    if request.method == 'POST':
        if reserva.estado == 'PENDIENTE':
            reserva.delete()
            messages.success(request, 'Solicitud eliminada.')
        else:
            motivo = request.POST.get('motivo_cancelacion')
            reserva.estado = 'CANCELADA'
            if motivo:
                reserva.motivo_cancelacion = motivo
            reserva.save(update_fields=["estado", "motivo_cancelacion"])
            messages.warning(request, 'Reserva cancelada.')
    return redirect('reservas:listar_reservas')


@login_required
def aprobar_reserva(request, reserva_id):
    if not request.user.is_staff and request.user.rol != 'ADMIN':
        messages.error(request, 'No tienes permisos de administrador.')
        return redirect('home')

    reserva = get_object_or_404(Reserva, pk=reserva_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        confirmado = request.POST.get('confirmado')

        if action == 'APROBAR':
            conflictos_existentes = Reserva.objects.filter(
                espacio=reserva.espacio,
                fecha=reserva.fecha,
                estado='APROBADA'
            ).filter(
                Q(hora_inicio__lt=reserva.hora_fin) & Q(hora_fin__gt=reserva.hora_inicio)
            ).exclude(id=reserva.id)

            if conflictos_existentes.exists():
                messages.error(request, "Error: El espacio ya está ocupado por otra reserva aprobada.")
                return redirect('gestion_reservas')

            competencia = Reserva.objects.filter(
                espacio=reserva.espacio,
                fecha=reserva.fecha,
                estado='PENDIENTE'
            ).filter(
                Q(hora_inicio__lt=reserva.hora_fin) & Q(hora_fin__gt=reserva.hora_inicio)
            ).exclude(id=reserva.id)

            if competencia.exists() and confirmado != 'si':
                ids_conflictivos = ", ".join([f"#{r.id}" for r in competencia])
                csrf_token = request.POST.get('csrfmiddlewaretoken')

                try:
                    url_aprobar = reverse('aprobar_reserva', args=[reserva.id])
                except Exception:
                    url_aprobar = f"/administracion/reservas/aprobar/{reserva.id}/"

                msg_html = f"""
                    <div class="d-flex align-items-center justify-content-between flex-wrap gap-2">
                        <div>
                            <i class="bi bi-exclamation-triangle-fill fs-4 me-2"></i>
                            <strong>¡Conflicto Detectado!</strong><br>
                            Esta reserva choca con {competencia.count()} solicitudes pendientes (IDs: {ids_conflictivos}).
                            <br><small>Al aprobar esta, las demás serán rechazadas automáticamente.</small>
                        </div>
                        <form method="post" action="{url_aprobar}">
                            <input type="hidden" name="csrfmiddlewaretoken" value="{csrf_token}">
                            <input type="hidden" name="action" value="APROBAR">
                            <input type="hidden" name="confirmado" value="si">
                            <button type="submit" class="btn btn-warning btn-sm text-dark fw-bold border-dark shadow-sm">
                                <i class="bi bi-check-circle-fill me-1"></i> Confirmar y Aprobar
                            </button>
                        </form>
                    </div>
                """
                messages.warning(request, mark_safe(msg_html))
                return redirect('gestion_reservas')

            try:
                with transaction.atomic():
                    for rr in reserva.recursos_asociados.all():
                        ocupados = RecursoReserva.objects.filter(
                            recurso=rr.recurso,
                            reserva__estado='APROBADA',
                            reserva__fecha=reserva.fecha
                        ).filter(
                            Q(reserva__hora_inicio__lt=reserva.hora_fin) &
                            Q(reserva__hora_fin__gt=reserva.hora_inicio)
                        ).aggregate(total=Sum('cantidad'))['total'] or 0

                        if (rr.recurso.stock - ocupados) < rr.cantidad:
                            raise ValidationError(f"Stock insuficiente para {rr.recurso.nombre} en el horario solicitado.")

                    reserva.estado = 'APROBADA'
                    reserva.save(update_fields=["estado"])  # ✅ dispara signals

                    if competencia.exists():
                        motivo_rechazo = f"Sistema: Se aprobó una solicitud prioritaria (ID #{reserva.id})."
                        for r in competencia:
                            r.estado = 'RECHAZADA'
                            r.motivo_cancelacion = motivo_rechazo
                            r.save(update_fields=["estado", "motivo_cancelacion"])  # ✅ dispara signals

                        messages.success(request, f'Reserva #{reserva.id} APROBADA exitosamente.')
                    else:
                        messages.success(request, f'Reserva #{reserva.id} APROBADA exitosamente.')

            except ValidationError as e:
                messages.error(request, f'No se pudo aprobar: {e}')

        elif action == 'RECHAZAR':
            reserva.estado = 'RECHAZADA'
            reserva.save(update_fields=["estado"])  # ✅ dispara signals
            messages.warning(request, f'Reserva #{reserva.id} RECHAZADA.')

    return redirect('gestion_reservas')


@login_required
def cancelar_forzosamente(request, reserva_id):
    if request.user.rol != 'ADMIN' and not request.user.is_staff:
        return redirect('home')

    reserva = get_object_or_404(Reserva, pk=reserva_id)
    if request.method == 'POST':
        motivo = request.POST.get('motivo_cancelacion')

        reserva.estado = 'CANCELADA'
        if motivo:
            reserva.motivo_cancelacion = f"Cancelada por Admin: {motivo}"
        reserva.save(update_fields=["estado", "motivo_cancelacion"])  # ✅ dispara signals
        messages.warning(request, f'Reserva #{reserva_id} cancelada.')

    return redirect('gestion_reservas')


@login_required
def api_consultar_stock(request):
    recurso_id = request.GET.get('recurso_id')
    fecha = request.GET.get('fecha')
    hora_inicio = request.GET.get('hora_inicio')
    hora_fin = request.GET.get('hora_fin')

    if not all([recurso_id, fecha, hora_inicio, hora_fin]):
        return JsonResponse({'error': 'Faltan datos'}, status=400)

    try:
        recurso = Recurso.objects.get(id=recurso_id)

        ocupados = RecursoReserva.objects.filter(
            recurso=recurso,
            reserva__estado__in=['PENDIENTE', 'APROBADA'],
            reserva__fecha=fecha
        ).filter(
            Q(reserva__hora_inicio__lt=hora_fin) &
            Q(reserva__hora_fin__gt=hora_inicio)
        ).aggregate(total=Sum('cantidad'))['total'] or 0

        disponible = max(recurso.stock - ocupados, 0)
        return JsonResponse({'stock_real': disponible})

    except Recurso.DoesNotExist:
        return JsonResponse({'error': 'Recurso no encontrado'}, status=404)


@login_required
def api_reservas_calendario(request):
    reservas = Reserva.objects.filter(estado='APROBADA')
    eventos = []
    for r in reservas:
        eventos.append({
            'title': f"Ocupado: {r.espacio.nombre}",
            'start': f"{r.fecha}T{r.hora_inicio}",
            'end': f"{r.fecha}T{r.hora_fin}",
            'color': '#D71920',
            'allDay': False,
        })
    return JsonResponse(eventos, safe=False)
