from functools import wraps
import csv
import openpyxl 
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError 
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.db import IntegrityError, transaction 
from django.utils.safestring import mark_safe 
from django.urls import reverse
from datetime import timedelta

# --- IMPORTACIONES DE MODELOS ---
from reservas.models import Reserva, RecursoReserva 
from inventario.models import Espacio, Recurso

# --- IMPORTACIONES DE FORMULARIOS ---
from .forms import (
    CustomUserCreationForm, 
    AreaForm, 
    CarreraForm, 
    EditarUsuarioForm, 
    RecursoForm 
)

# --- API REST ---
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Area, Carrera 
from .serializers import UserSerializer, AreaSerializer, CarreraSerializer

User = get_user_model()

# ==============================================================================
# 1. DECORADOR DE SEGURIDAD PERSONALIZADO (BLINDAJE)
# ==============================================================================

def admin_required(view_func):
    """
    Decorador personalizado: Si el usuario NO es admin, lo manda al Home.
    Evita el bucle de redirección al login si ya estás logueado.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Si no está logueado, al login
        if not request.user.is_authenticated:
            return redirect('login')
        
        # 2. Si está logueado pero NO es ADMIN, al home con error
        if getattr(request.user, 'rol', '') != 'ADMIN' and not request.user.is_superuser:
            messages.error(request, 'Acceso denegado: No tienes permisos de administrador.')
            return redirect('home')
        
        # 3. Si es Admin, pasa
        return view_func(request, *args, **kwargs)
        
    return _wrapped_view

# ==============================================================================
# 2. VISTAS GENERALES
# ==============================================================================

@login_required
def home(request):
    if request.user.rol == 'ADMIN':
        return redirect('admin_dashboard')
    
    hoy = timezone.localdate()
    
    # ----------------------------------------------------------------------
    # DASHBOARD DE USUARIO (MISMO LOOK DEL ADMIN, PERO CON DATOS PERSONALES)
    # ----------------------------------------------------------------------
    if request.user.rol == 'SOLICITANTE':
        reservas_hoy = Reserva.objects.filter(solicitante=request.user, fecha=hoy).count()
        pendientes = Reserva.objects.filter(solicitante=request.user, estado='PENDIENTE').count()
        aprobadas = Reserva.objects.filter(solicitante=request.user, estado='APROBADA').count()
        rechazadas = Reserva.objects.filter(solicitante=request.user, estado='RECHAZADA').count()
        ultimas_reservas = Reserva.objects.filter(solicitante=request.user).order_by('-fecha_solicitud')[:5]

        # --- GRÁFICO 1: Actividad personal últimos 7 días ---
        today = timezone.now().date()
        fechas_grafico = []
        datos_grafico = []
        for i in range(6, -1, -1):
            fecha = today - timedelta(days=i)
            count = Reserva.objects.filter(solicitante=request.user, fecha=fecha).count()
            fechas_grafico.append(fecha.strftime("%d/%m"))
            datos_grafico.append(count)

        # --- GRÁFICO 2: Top 5 Recursos solicitados por el usuario ---
        top_recursos_qs = RecursoReserva.objects.filter(reserva__solicitante=request.user) \
            .values('recurso__nombre') \
            .annotate(total_pedidos=Sum('cantidad')) \
            .order_by('-total_pedidos')[:5]

        recursos_labels = [item['recurso__nombre'] for item in top_recursos_qs]
        recursos_data = [item['total_pedidos'] for item in top_recursos_qs]

        # --- GRÁFICO 3: Mis solicitudes por estado ---
        estados_labels = dates_to_json_list(["Pendiente", "Aprobada", "Rechazada"])
        estados_data = [pendientes, aprobadas, rechazadas]
    else:
        # Roles distintos a SOLICITANTE (ej: MANTENIMIENTO): dashboard informativo
        reservas_hoy = 0
        pendientes = 0
        aprobadas = 0
        rechazadas = 0
        ultimas_reservas = []
        fechas_grafico = [timezone.now().strftime("%d/%m")]
        datos_grafico = [0]
        recursos_labels = []
        recursos_data = []
        estados_labels = dates_to_json_list(["Pendiente", "Aprobada", "Rechazada"])
        estados_data = [0, 0, 0]
    
    kpi_espacios_disponibles = Espacio.objects.filter(activo=True).count()
    kpi_recursos = Recurso.objects.count() 
    
    context = {
        'kpi_reservas_hoy': reservas_hoy,
        'kpi_pendientes': pendientes,
        'kpi_aprobadas': aprobadas,
        'kpi_rechazadas': rechazadas,
        'ultimas_reservas': ultimas_reservas,
        'kpi_espacios_disponibles': kpi_espacios_disponibles,
        'kpi_recursos': kpi_recursos,
        # Datos para gráficos (mismo layout que el dashboard admin)
        'chart_labels': dates_to_json_list(fechas_grafico),
        'chart_data': datos_grafico,
        'recursos_labels': dates_to_json_list(recursos_labels),
        'recursos_data': recursos_data,
        'estados_labels': estados_labels,
        'estados_data': estados_data,
        'ultima_sync': timezone.now()
    }
    return render(request, 'core/home.html', context)

# ==============================================================================
# 3. ADMINISTRACIÓN
# ==============================================================================

@admin_required
def admin_dashboard(request):
    # --- KPIs Básicos ---
    pending_count = Reserva.objects.filter(estado='PENDIENTE').count()
    approved_count = Reserva.objects.filter(estado='APROBADA').count()
    rejected_count = Reserva.objects.filter(estado='RECHAZADA').count()
    total_spaces = Espacio.objects.filter(activo=True).count()
    
    # --- Recursos Críticos (Stock bajo) ---
    critical_resources = Recurso.objects.filter(stock__lte=5).count()

    # --- GRÁFICO 1: Actividad últimos 7 días ---
    today = timezone.now().date()
    fechas_grafico = []
    datos_grafico = []
    for i in range(6, -1, -1):
        fecha = today - timedelta(days=i)
        count = Reserva.objects.filter(fecha=fecha).count()
        nombre_dia = fecha.strftime("%d/%m") 
        fechas_grafico.append(nombre_dia)
        datos_grafico.append(count)

    # --- GRÁFICO 2: Top 5 Recursos Más Solicitados ---
    top_recursos_qs = RecursoReserva.objects.values('recurso__nombre') \
        .annotate(total_pedidos=Sum('cantidad')) \
        .order_by('-total_pedidos')[:5]
    
    recursos_labels = [item['recurso__nombre'] for item in top_recursos_qs]
    recursos_data = [item['total_pedidos'] for item in top_recursos_qs]

    # --- GRÁFICO 3: Reservas por Área Académica ---
    areas_qs = Reserva.objects.values('solicitante__area__nombre') \
        .exclude(solicitante__area__isnull=True) \
        .annotate(total=Count('id')) \
        .order_by('-total')
    
    areas_labels = [item['solicitante__area__nombre'] for item in areas_qs]
    areas_data = [item['total'] for item in areas_qs]

    context = {
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'total_spaces': total_spaces,
        'critical_resources': critical_resources,
        'chart_labels': dates_to_json_list(fechas_grafico),
        'chart_data': datos_grafico,
        'recursos_labels': dates_to_json_list(recursos_labels),
        'recursos_data': recursos_data,
        'areas_labels': dates_to_json_list(areas_labels),
        'areas_data': areas_data,
    }
    return render(request, 'administracion/dashboard.html', context)

def dates_to_json_list(lista):
    return lista 

# --- EXPORTAR EXCEL CON FECHA EN NOMBRE ---
@admin_required
def export_reservas_excel(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    
    fecha_hoy = timezone.now().strftime("%d-%m-%Y")
    filename = f"Reporte_Reservas_{fecha_hoy}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reservas"

    headers = ['ID', 'Solicitante', 'RUT', 'Área', 'Correo', 'Espacio', 'Fecha', 'Inicio', 'Fin', 'Estado', 'Recursos Adicionales', 'Motivo']
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
            r.id, f"{r.solicitante.first_name} {r.solicitante.last_name}", 
            r.solicitante.rut, r.solicitante.nombre_area, r.solicitante.email, 
            r.espacio.nombre, r.fecha, r.hora_inicio, r.hora_fin, 
            r.get_estado_display(), recursos_str if recursos_str else "N/A", r.motivo
        ]
        ws.append(row)

    for column_cells in ws.columns:
        length = max(len(str(cell.value) or "") for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2

    wb.save(response)
    return response

@admin_required
def export_reservas_csv(request):
    qs = Reserva.objects.all().order_by('-fecha')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="reservas_export.csv"'
    writer = csv.writer(response)
    writer.writerow(['id', 'solicitante', 'rut', 'area', 'espacio', 'fecha', 'hora', 'estado'])
    for r in qs:
        writer.writerow([r.id, r.solicitante.email, r.solicitante.rut, r.solicitante.nombre_area, r.espacio.nombre, r.fecha, r.hora_inicio, r.estado])
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
    context = {'reservas': qs, 'filtro_actual': estado_filter, 'con_archivo': con_archivo}
    return render(request, 'administracion/gestion_reservas.html', context)

@admin_required
def aprobar_reserva(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        confirmado = request.POST.get('confirmado') 
        if action == 'APROBAR':
            # Verificar conflictos físicos (YA APROBADAS)
            conflictos_existentes = Reserva.objects.filter(
                espacio=reserva.espacio, fecha=reserva.fecha, estado='APROBADA'
            ).filter(
                Q(hora_inicio__lt=reserva.hora_fin) & Q(hora_fin__gt=reserva.hora_inicio)
            ).exclude(id=reserva.id)

            if conflictos_existentes.exists():
                messages.error(request, "Error: El espacio ya está ocupado por otra reserva aprobada.")
                return redirect('gestion_reservas')

            # Verificar conflictos de competencia (PENDIENTES)
            competencia = Reserva.objects.filter(
                espacio=reserva.espacio, fecha=reserva.fecha, estado='PENDIENTE'
            ).filter(
                Q(hora_inicio__lt=reserva.hora_fin) & Q(hora_fin__gt=reserva.hora_inicio)
            ).exclude(id=reserva.id)

            if competencia.exists() and confirmado != 'si':
                ids_conflictivos = ", ".join([f"#{r.id}" for r in competencia])
                csrf_token = request.POST.get('csrfmiddlewaretoken')
                try:
                    url_aprobar = reverse('aprobar_reserva', args=[reserva.id])
                except:
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
                            recurso=rr.recurso, reserva__estado='APROBADA', reserva__fecha=reserva.fecha
                        ).filter(
                            Q(reserva__hora_inicio__lt=reserva.hora_fin) & Q(reserva__hora_fin__gt=reserva.hora_inicio)
                        ).aggregate(total=Sum('cantidad'))['total'] or 0
                        
                        if (rr.recurso.stock - ocupados) < rr.cantidad:
                             raise ValidationError(f"Stock insuficiente para {rr.recurso.nombre} en el horario solicitado.")
                    
                    reserva.estado = 'APROBADA'
                    reserva.save()
                    
                    if competencia.exists():
                        motivo_rechazo = f"Sistema: Se aprobó una solicitud prioritaria (ID #{reserva.id})."
                        competencia.update(estado='RECHAZADA', motivo_cancelacion=motivo_rechazo)
                        messages.success(request, f'Reserva #{reserva.id} APROBADA. Conflictos rechazados.')
                    else:
                        messages.success(request, f'Reserva #{reserva.id} APROBADA exitosamente.')

            except ValidationError as e:
                messages.error(request, f'No se pudo aprobar: {e.message}')
        elif action == 'RECHAZAR':
            reserva.estado = 'RECHAZADA'
            reserva.save()
            messages.warning(request, f'Reserva #{reserva.id} RECHAZADA.')
    return redirect('gestion_reservas')

@admin_required
def cancelar_forzosamente(request, reserva_id):
    reserva = get_object_or_404(Reserva, pk=reserva_id)
    if request.method == 'POST':
        motivo = request.POST.get('motivo_cancelacion')
        if reserva.estado != 'FINALIZADA':
            reserva.estado = 'CANCELADA'
            if motivo:
                reserva.motivo_cancelacion = f"Cancelada por Admin: {motivo}"
            reserva.save()
            messages.warning(request, f'Reserva #{reserva_id} cancelada.')
    return redirect('gestion_reservas')

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
                messages.error(request, 'Error: Usuario ya registrado.')
            except Exception as e:
                messages.error(request, f'Error: {e}')
        else:
            messages.error(request, 'Corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'administracion/crear_usuario.html', {'form': form})

@admin_required
def editar_usuario(request, user_id):
    usuario_a_editar = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = EditarUsuarioForm(request.POST, instance=usuario_a_editar)
        if form.is_valid():
            user = form.save(commit=False)
            rol = form.cleaned_data.get('rol')
            area_seleccionada = form.cleaned_data.get('area')
            
            if rol in ['ADMIN', 'SOLICITANTE']:
                user.area = area_seleccionada
                user.carrera = None
            
            user.save()
            messages.success(request, 'Usuario actualizado.')
            return redirect('gestion_usuarios')
    else:
        form = EditarUsuarioForm(instance=usuario_a_editar)
    return render(request, 'administracion/editar_usuario.html', {'form': form, 'usuario': usuario_a_editar})

# --- GESTIÓN DE ÁREAS Y CARRERAS ---

@admin_required
def gestion_areas(request):
    areas = Area.objects.all().order_by('nombre')
    return render(request, 'administracion/gestion_areas.html', {'areas': areas})

@admin_required
def crear_area(request):
    if request.method == 'POST':
        form = AreaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Área creada.')
            return redirect('gestion_areas')
    else:
        form = AreaForm()
    return render(request, 'administracion/crear_area.html', {'form': form})

@admin_required
def editar_area(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    if request.method == 'POST':
        form = AreaForm(request.POST, instance=area)
        if form.is_valid():
            form.save()
            messages.success(request, 'Área actualizada.')
            return redirect('gestion_areas')
    else:
        form = AreaForm(instance=area)
    return render(request, 'administracion/crear_area.html', {'form': form})

@admin_required
def eliminar_area(request, area_id):
    area = get_object_or_404(Area, pk=area_id)
    area.delete()
    messages.warning(request, 'Área eliminada.')
    return redirect('gestion_areas')

@admin_required
def gestion_carreras(request):
    carreras = Carrera.objects.all().select_related('area').order_by('area__nombre', 'nombre')
    return render(request, 'administracion/gestion_carreras.html', {'carreras': carreras})

@admin_required
def crear_carrera(request):
    if request.method == 'POST':
        form = CarreraForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Carrera creada.')
            return redirect('gestion_carreras')
    else:
        form = CarreraForm()
    return render(request, 'administracion/crear_carrera.html', {'form': form})

@admin_required
def editar_carrera(request, carrera_id):
    carrera = get_object_or_404(Carrera, pk=carrera_id)
    if request.method == 'POST':
        form = CarreraForm(request.POST, instance=carrera)
        if form.is_valid():
            form.save()
            messages.success(request, 'Carrera actualizada.')
            return redirect('gestion_carreras')
    else:
        form = CarreraForm(instance=carrera)
    return render(request, 'administracion/crear_carrera.html', {'form': form})

@admin_required
def eliminar_carrera(request, carrera_id):
    carrera = get_object_or_404(Carrera, pk=carrera_id)
    carrera.delete()
    messages.warning(request, 'Carrera eliminada.')
    return redirect('gestion_carreras')

# --- GESTIÓN DE INVENTARIO ---

@admin_required
def gestion_inventario(request):
    if request.method == 'POST' and request.POST.get('action') == 'crear':
        try:
            form = RecursoForm(request.POST)
            if form.is_valid():
                recurso = form.save(commit=False)
                if request.user.area:
                    recurso.area = request.user.area
                recurso.save()
                messages.success(request, "Recurso creado correctamente.")
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
        except Exception as e:
            messages.error(request, f"Error al crear: {e}")
        return redirect('gestion_inventario')

    espacios = Espacio.objects.all()
    
    # FILTRO POR ÁREA DE ADMIN
    if request.user.is_superuser:
        recursos = Recurso.objects.all().order_by('nombre')
    elif request.user.area:
        recursos = Recurso.objects.filter(area=request.user.area).order_by('nombre')
    else:
        # Caso Admin sin área
        recursos = Recurso.objects.none()

    return render(request, 'inventario/recursos.html', {'espacios': espacios, 'recursos': recursos})

@admin_required
def editar_recurso(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    if request.method == 'POST':
        form = RecursoForm(request.POST, instance=recurso)
        if form.is_valid():
            form.save()
            messages.success(request, 'Recurso actualizado.')
            return redirect('gestion_inventario')
    else:
        form = RecursoForm(instance=recurso)
    return render(request, 'inventario/editar_recurso.html', {'form': form, 'recurso': recurso})

@admin_required
def eliminar_recurso(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    try:
        recurso.delete()
        messages.success(request, 'Recurso eliminado.')
    except Exception as e:
        messages.error(request, 'No se puede eliminar (tiene reservas asociadas).')
    return redirect('gestion_inventario')

@admin_required
def espacio_set_estado(request, espacio_id):
    if request.method == 'POST':
        espacio = get_object_or_404(Espacio, pk=espacio_id)
        espacio.activo = not espacio.activo
        espacio.save()
        messages.success(request, f'Estado de {espacio.nombre} actualizado.')
    return redirect('gestion_inventario')

# ==============================================================================
# 4. API VIEWSETS
# ==============================================================================

class AreaViewSet(viewsets.ModelViewSet):
    queryset = Area.objects.all()
    serializer_class = AreaSerializer
    permission_classes = [IsAuthenticated]

class CarreraViewSet(viewsets.ModelViewSet):
    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Carrera.objects.all()
        area_id = self.request.query_params.get('area_id')
        if area_id is not None:
            queryset = queryset.filter(area_id=area_id)
        return queryset

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

# ======================================================================
# 5. API STOCK EN TIEMPO REAL
# ======================================================================

@login_required
def api_stock_actual(request):
    """
    Retorna JSON con stock disponible.
    (Fix) No rompe si Recurso NO tiene campo 'area'.
    """
    fecha_str = request.GET.get('fecha')
    hora_inicio_str = request.GET.get('hora_inicio')
    hora_fin_str = request.GET.get('hora_fin')

    # ✅ Helper: Recurso tiene campo "area"?
    def recurso_tiene_area() -> bool:
        try:
            return any(getattr(f, "name", None) == "area" for f in Recurso._meta.get_fields())
        except Exception:
            return False

    # ✅ Por defecto, TODOS ven todos los recursos (para que no se rompa)
    recursos = Recurso.objects.all()

    # (Opcional futuro) si algún día agregas area a Recurso, esto filtrará por área automáticamente
    if (
        request.user.is_authenticated
        and not request.user.is_superuser
        and getattr(request.user, "area_id", None)
        and recurso_tiene_area()
    ):
        recursos = Recurso.objects.filter(area=request.user.area)

    data = []

    for r in recursos.order_by("nombre"):
        ocupados = 0

        if fecha_str and hora_inicio_str and hora_fin_str:
            reservas_conflicto = Reserva.objects.filter(
                fecha=fecha_str,
                estado__in=['PENDIENTE', 'APROBADA']
            ).filter(
                Q(hora_inicio__lt=hora_fin_str) & Q(hora_fin__gt=hora_inicio_str)
            )

            if reservas_conflicto.exists():
                ocupados = RecursoReserva.objects.filter(
                    reserva__in=reservas_conflicto,
                    recurso=r
                ).aggregate(total=Sum('cantidad'))['total'] or 0

        stock_total = int(r.stock or 0)
        ocupado_total = int(ocupados or 0)
        disponible = stock_total - ocupado_total

        data.append({
            'id': r.id,
            'nombre': r.nombre,
            'total': stock_total,
            'disponible': max(disponible, 0)
        })

    return JsonResponse({'recursos': data})


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