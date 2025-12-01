import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.safestring import mark_safe # Importante para el HTML en mensajes

from .forms import ReservaForm
from .models import Reserva, ReservaRecurso
from inventario.models import Recurso, Espacio

# ==============================================================================
# CREAR RESERVA
# ==============================================================================
@login_required
def crear_reserva(request):
    # NOTA: Se eliminó la restricción de rol 'MANTENIMIENTO'
    
    recursos_disponibles = Recurso.objects.filter(stock__gt=0)
    espacios_activos = Espacio.objects.filter(activo=True)

    if request.method == 'POST':
        form = ReservaForm(request.POST, request.FILES)
        recursos_json = request.POST.get('recursos_seleccionados')
        if not recursos_json or not recursos_json.strip():
            recursos_json = '[]'

        if form.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar la Reserva base
                    reserva = form.save(commit=False)
                    reserva.solicitante = request.user
                    reserva.save() 

                    # 2. Procesar los Recursos seleccionados
                    lista_recursos = json.loads(recursos_json)
                    for item in lista_recursos:
                        recurso_id = int(item['id'])
                        cantidad = int(item['cantidad'])

                        # Validar Stock Real (Bloqueo de base de datos para concurrencia)
                        recurso_db = Recurso.objects.select_for_update().get(id=recurso_id)
                        if recurso_db.stock < cantidad:
                            raise ValueError(f"Stock insuficiente para {recurso_db.nombre}.")

                        ReservaRecurso.objects.create(
                            reserva=reserva,
                            recurso=recurso_db,
                            cantidad=cantidad
                        )

                    messages.success(request, 'Solicitud de reserva creada con éxito. Esperando aprobación.')
                    return redirect('reservas:listar_reservas')

            except json.JSONDecodeError:
                messages.error(request, "Error técnico: Formato de recursos inválido.")
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error al procesar la solicitud: {e}")
        
        else:
            # --- CONSTRUCCIÓN DE MENSAJE DE ERROR DETALLADO ---
            errores_html = ""
            for field, errors in form.errors.items():
                if field == '__all__':
                    label = "Error General"
                else:
                    label = form.fields[field].label or field.replace('_', ' ').title()
                
                for error in errors:
                    errores_html += f"<li><strong>{label}:</strong> {error}</li>"
            
            messages.error(request, mark_safe(f"""
                <div class="d-flex align-items-center">
                    <i class="bi bi-exclamation-triangle-fill fs-3 me-3"></i>
                    <div>
                        <strong>No pudimos crear la solicitud.</strong>
                        <ul class="mb-0 ps-3 mt-1" style="font-size: 0.9rem;">
                            {errores_html}
                        </ul>
                    </div>
                </div>
            """))

    else:
        form = ReservaForm()

    context = {
        'form': form,
        'recursos': recursos_disponibles, 
        'espacios': espacios_activos,     
    }
    return render(request, 'reservas/crear_reserva.html', context)

# ==============================================================================
# LISTAR (MIS RESERVAS)
# ==============================================================================
@login_required
def listar_reservas(request):
    qs = Reserva.objects.filter(solicitante=request.user).order_by('-fecha', '-hora_inicio')
    paginator = Paginator(qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'reservas/listar_reservas.html', {'reservas': page_obj.object_list, 'page_obj': page_obj})

# ==============================================================================
# DETALLE, EDITAR Y CANCELAR
# ==============================================================================
@login_required
def detalle_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva.objects.prefetch_related('recursos_asociados__recurso'), pk=reserva_id, solicitante=request.user)
    return render(request, 'reservas/detalle_reserva.html', {'reserva': reserva})

@login_required
def editar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, solicitante=request.user)
    
    # IMPORTANTE: Necesitamos los espacios para pintar las fotos en el selector visual
    espacios_activos = Espacio.objects.filter(activo=True)
    recursos_disponibles = Recurso.objects.filter(stock__gt=0)
    
    # Preparamos los recursos actuales para que el JS los cargue en la tabla
    recursos_preexistentes = []
    for rr in reserva.recursos_asociados.all():
        recursos_preexistentes.append({'id': str(rr.recurso.id), 'nombre': rr.recurso.nombre, 'cantidad': rr.cantidad})

    if reserva.estado != 'PENDIENTE':
        messages.error(request, 'No puedes editar una reserva ya procesada.')
        return redirect('reservas:listar_reservas')

    if request.method == 'POST':
        form = ReservaForm(request.POST, request.FILES, instance=reserva)
        recursos_json = request.POST.get('recursos_seleccionados', '[]')
        if not recursos_json.strip(): recursos_json = '[]'

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    
                    # Actualización de Recursos: Borrón y cuenta nueva
                    reserva.recursos_asociados.all().delete()
                    
                    lista_recursos = json.loads(recursos_json)
                    for item in lista_recursos:
                        recurso_db = Recurso.objects.select_for_update().get(id=int(item['id']))
                        cantidad = int(item['cantidad'])
                        
                        if recurso_db.stock < cantidad: 
                            raise ValueError(f"Stock insuficiente para {recurso_db.nombre}")
                        
                        ReservaRecurso.objects.create(reserva=reserva, recurso=recurso_db, cantidad=cantidad)
                    
                    messages.success(request, 'Reserva actualizada correctamente.')
                    return redirect('reservas:listar_reservas')
            except ValueError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f'Error al actualizar: {e}')
        else:
            # --- CONSTRUCCIÓN DE MENSAJE DE ERROR PARA EDICIÓN ---
            errores_html = ""
            for field, errors in form.errors.items():
                if field == '__all__':
                    label = "Error General"
                else:
                    label = form.fields[field].label or field.replace('_', ' ').title()
                
                for error in errors:
                    errores_html += f"<li><strong>{label}:</strong> {error}</li>"
            
            messages.error(request, mark_safe(f"""
                <div class="d-flex align-items-center">
                    <i class="bi bi-pencil-square fs-3 me-3"></i>
                    <div>
                        <strong>No se pudieron guardar los cambios.</strong>
                        <ul class="mb-0 ps-3 mt-1" style="font-size: 0.9rem;">
                            {errores_html}
                        </ul>
                    </div>
                </div>
            """))
    else:
        form = ReservaForm(instance=reserva)
    
    context = {
        'form': form, 
        'reserva': reserva, 
        'recursos_disponibles': recursos_disponibles, 
        'recursos_preexistentes': recursos_preexistentes,
        'espacios': espacios_activos # <--- CLAVE PARA QUE SE VEAN LAS FOTOS
    }
    return render(request, 'reservas/editar_reserva.html', context)

@login_required
def cancelar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id, solicitante=request.user)
    if request.method == 'POST':
        if reserva.estado == 'PENDIENTE':
            reserva.delete()
            messages.success(request, 'Solicitud eliminada correctamente.')
        else:
            reserva.estado = 'CANCELADA'
            reserva.save()
            messages.warning(request, 'Reserva cancelada.')
    return redirect('reservas:listar_reservas')

# ==============================================================================
# API JSON (Para validación en tiempo real con Fetch)
# ==============================================================================
def api_consultar_stock(request):
    recurso_id = request.GET.get('recurso_id')
    fecha = request.GET.get('fecha')
    hora_inicio = request.GET.get('hora_inicio')
    hora_fin = request.GET.get('hora_fin')
    
    if not all([recurso_id, fecha, hora_inicio, hora_fin]):
        return JsonResponse({'error': 'Faltan datos'}, status=400)
    
    try:
        recurso = Recurso.objects.get(id=recurso_id)
        
        # Reservas aprobadas que se solapan en horario
        reservas_en_conflicto = Reserva.objects.filter(
            fecha=fecha,
            estado='APROBADA'
        ).filter(
            Q(hora_inicio__lt=hora_fin) & Q(hora_fin__gt=hora_inicio)
        )
        
        consumido = ReservaRecurso.objects.filter(
            reserva__in=reservas_en_conflicto,
            recurso=recurso
        ).aggregate(total=Sum('cantidad'))['total'] or 0
        
        return JsonResponse({'stock_real': recurso.stock - consumido})
        
    except Recurso.DoesNotExist:
        return JsonResponse({'error': 'Recurso no encontrado'}, status=404)

# ==============================================================================
# API CALENDARIO (NUEVO: Para que FullCalendar tenga datos)
# ==============================================================================
@login_required
def api_reservas_calendario(request):
    # Obtener solo reservas APROBADAS para mostrar ocupación
    reservas = Reserva.objects.filter(estado='APROBADA')
    
    eventos = []
    for r in reservas:
        eventos.append({
            'title': f"Ocupado: {r.espacio.nombre}",
            'start': f"{r.fecha}T{r.hora_inicio}",
            'end': f"{r.fecha}T{r.hora_fin}",
            'color': '#D71920', # Rojo corporativo para indicar no disponible
            'allDay': False,
        })
    
    return JsonResponse(eventos, safe=False)