from functools import wraps
import csv
import openpyxl 
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from django.db import IntegrityError
from datetime import timedelta

# --- IMPORTACIONES DE TUS APLICACIONES ---
from reservas.models import Reserva
from inventario.models import Espacio, Recurso
from .forms import CustomUserCreationForm

User = get_user_model()

# ==============================================================================
# 1. DECORADORES DE SEGURIDAD (RBAC)
# ==============================================================================

def user_passes_test(test_func, login_url=None, redirect_field_name=REDIRECT_FIELD_NAME):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if test_func(request.user):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return wrapper
    return decorator

def is_admin(user):
    return user.is_active and getattr(user, 'rol', '') == 'ADMIN'

def admin_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url='login'):
    actual_decorator = user_passes_test(
        is_admin,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

# ==============================================================================
# 2. VISTAS GENERALES (DASHBOARD USUARIO - SOLICITANTE)
# ==============================================================================

@login_required
def home(request):
    # Si es Admin, redirigir a su dashboard específico
    if request.user.rol == 'ADMIN':
        return redirect('admin_dashboard')
    
    hoy = timezone.localdate()
    
    # Lógica para el Dashboard del SOLICITANTE (Antes Coordinador)
    if request.user.rol == 'SOLICITANTE':
        reservas_hoy = Reserva.objects.filter(solicitante=request.user, fecha=hoy).count()
        pendientes = Reserva.objects.filter(solicitante=request.user, estado='PENDIENTE').count()
        ultimas_reservas = Reserva.objects.filter(solicitante=request.user).order_by('-fecha_solicitud')[:5]
    else:
        # Fallback por seguridad (ej: si quedara algún usuario con rol viejo)
        reservas_hoy = 0
        pendientes = 0
        ultimas_reservas = []
    
    # KPIs generales visibles para el solicitante
    kpi_espacios_disponibles = Espacio.objects.filter(activo=True).count()
    kpi_recursos = Recurso.objects.count() 
    
    context = {
        'kpi_reservas_hoy': reservas_hoy,
        'kpi_pendientes': pendientes,
        'ultimas_reservas': ultimas_reservas,
        'kpi_espacios_disponibles': kpi_espacios_disponibles,
        'kpi_recursos': kpi_recursos,
        'ultima_sync': timezone.now()
    }
    return render(request, 'core/home.html', context)

# ==============================================================================
# 3. VISTAS DE ADMINISTRACIÓN (DASHBOARD Y GESTIÓN)
# ==============================================================================

@admin_required
def admin_dashboard(request):
    # KPIs Básicos
    pending_count = Reserva.objects.filter(estado='PENDIENTE').count()
    approved_count = Reserva.objects.filter(estado='APROBADA').count()
    rejected_count = Reserva.objects.filter(estado='RECHAZADA').count()
    total_spaces = Espacio.objects.filter(activo=True).count()
    critical_resources = Recurso.objects.filter(stock__lte=5).count()
    recent_reservas = Reserva.objects.all().order_by('-fecha_solicitud')[:5]

    # --- LÓGICA PARA EL GRÁFICO DE ACTIVIDAD (Últimos 7 días) ---
    today = timezone.now().date()
    fechas_grafico = []
    datos_grafico = []
    
    for i in range(6, -1, -1):
        fecha = today - timedelta(days=i)
        count = Reserva.objects.filter(fecha=fecha).count()
        nombre_dia = fecha.strftime("%d/%m") 
        fechas_grafico.append(nombre_dia)
        datos_grafico.append(count)

    context = {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_spaces': total_spaces,
        'critical_resources': critical_resources,
        'recent_reservas': recent_reservas,
        'chart_labels': dates_to_json_list(fechas_grafico),
        'chart_data': datos_grafico,
    }
    return render(request, 'administracion/dashboard.html', context)

def dates_to_json_list(lista):
    return lista 

# --- REPORTE EXCEL PROFESIONAL ---
@admin_required
def export_reservas_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="Reporte_Reservas_INACAP.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reservas"

    headers = ['ID', 'Solicitante', 'Correo', 'Espacio', 'Fecha', 'Inicio', 'Fin', 'Estado', 'Recursos Adicionales', 'Motivo']
    ws.append(headers)

    header_fill = PatternFill(start_color="D71920", end_color="D71920", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    thin_border = Border(left=Side(style='thin'), right=Side(style='thin'), top=Side(style='thin'), bottom=Side(style='thin'))

    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin_border

    reservas = Reserva.objects.all().order_by('-fecha')
    for r in reservas:
        recursos_str = ", ".join([f"{rr.cantidad}x {rr.recurso.nombre}" for rr in r.recursos_asociados.all()])
        
        row = [
            r.id,
            f"{r.solicitante.first_name} {r.solicitante.last_name}",
            r.solicitante.email,
            r.espacio.nombre,
            r.fecha,
            r.hora_inicio,
            r.hora_fin,
            r.get_estado_display(),
            recursos_str if recursos_str else "N/A",
            r.motivo
        ]
        ws.append(row)

    for column_cells in ws.columns:
        length = max(len(str(cell.value) or "") for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    wb.save(response)
    return response

# --- GESTIÓN DE RESERVAS ---

@admin_required
def gestion_reservas(request):
    estado_filter = request.GET.get('estado', 'TODAS')
    con_archivo = request.GET.get('con_archivo') 

    qs = Reserva.objects.all().order_by('-fecha', '-hora_inicio')

    if estado_filter != 'TODAS':
        qs = qs.filter(estado=estado_filter)

    if con_archivo == 'si':
        qs = qs.exclude(archivo_adjunto='')

    context = {
        'reservas': qs,
        'filtro_actual': estado_filter,
        'con_archivo': con_archivo,
    }
    return render(request, 'administracion/gestion_reservas.html', context)

@admin_required
def aprobar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'APROBAR':
            reserva.estado = 'APROBADA'
            reserva.save()
            messages.success(request, f'Reserva #{reserva.id} APROBADA exitosamente.')
        elif action == 'RECHAZAR':
            reserva.estado = 'RECHAZADA'
            reserva.save()
            messages.warning(request, f'Reserva #{reserva.id} RECHAZADA.')
    return redirect('gestion_reservas')

@admin_required
def cancelar_forzosamente(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    
    if request.method == 'POST':
        # Capturamos el motivo del formulario
        motivo = request.POST.get('motivo_cancelacion')
        
        if reserva.estado != 'FINALIZADA':
            reserva.estado = 'CANCELADA'
            
            # Guardamos el motivo añadiendo quién lo hizo
            if motivo:
                reserva.motivo_cancelacion = f"Cancelada por Admin: {motivo}"
            else:
                reserva.motivo_cancelacion = "Cancelada por Admin sin motivo especificado."
                
            reserva.save()
            messages.warning(request, f'Reserva #{reserva_id} cancelada correctamente.')
            
    return redirect('gestion_reservas')

# Mantener para compatibilidad (si se usaba en enlaces viejos), pero export_reservas_excel es la principal
@admin_required
def export_reservas_csv(request):
    qs = Reserva.objects.all().order_by('-fecha')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reservas_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'solicitante', 'espacio', 'fecha', 'hora', 'estado'])
    for r in qs:
        writer.writerow([r.id, r.solicitante.email, r.espacio.nombre, r.fecha, r.hora_inicio, r.estado])
    return response

# --- GESTIÓN DE USUARIOS ---

@admin_required
def gestion_usuarios(request):
    q = request.GET.get('q', '').strip()
    users = User.objects.all().order_by('rol', 'email')
    if q:
        users = users.filter(Q(username__icontains=q) | Q(email__icontains=q))
    return render(request, 'administracion/gestion_usuarios.html', {'users': users})

@admin_required
def gestionar_rol_estado(request, user_id):
    user_target = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        value = request.POST.get('value')
        if action == 'rol':
            user_target.rol = value
            messages.success(request, f'Rol actualizado.')
        elif action == 'toggle_active':
            user_target.is_active = not user_target.is_active
            messages.warning(request, f'Estado actualizado.')
        user_target.save()
    return redirect('gestion_usuarios')

@admin_required
def crear_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                messages.success(request, f'Usuario {user.username} creado correctamente.')
                return redirect('gestion_usuarios')
            except IntegrityError:
                messages.error(request, 'Error: El nombre de usuario o correo ya está registrado.')
            except Exception as e:
                messages.error(request, f'Error al crear usuario: {e}')
        else:
            messages.error(request, 'Por favor, corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'administracion/crear_usuario.html', {'form': form})

# --- GESTIÓN DE INVENTARIO ---

@admin_required
def gestion_inventario(request):
    espacios = Espacio.objects.all()
    recursos = Recurso.objects.all()
    # Apunta al template correcto de inventario
    return render(request, 'inventario/recursos.html', {'espacios': espacios, 'recursos': recursos})

@admin_required
def espacio_set_estado(request, espacio_id):
    if request.method == 'POST':
        espacio = get_object_or_404(Espacio, pk=espacio_id)
        espacio.activo = not espacio.activo
        espacio.save()
        messages.success(request, f'Estado de {espacio.nombre} actualizado.')
    return redirect('gestion_inventario')