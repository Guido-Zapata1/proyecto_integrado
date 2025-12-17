from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.utils import timezone
from core.views import admin_required  # Importamos el decorador de seguridad
from .models import Espacio, Recurso

# ==============================================================================
# GESTIÓN DE ESPACIOS
# ==============================================================================

@admin_required
def gestion_espacios(request):
    # 1. Lógica para CREAR un espacio
    if request.method == "POST":
        nombre = request.POST.get('nombre')
        ubicacion = request.POST.get('ubicacion')
        capacidad = request.POST.get('capacidad')
        imagen = request.FILES.get('imagen') 

        try:
            Espacio.objects.create(
                nombre=nombre,
                ubicacion=ubicacion,
                capacidad=capacidad,
                imagen=imagen
            )
            messages.success(request, "Espacio creado correctamente.")
            return redirect("inventario:gestion_espacios")
        except Exception as e:
            messages.error(request, f"Error al crear espacio: {e}")

    # 2. Lógica para LISTAR espacios
    espacios = Espacio.objects.all().order_by('nombre')
    return render(request, "inventario/espacios.html", {"espacios": espacios})

@admin_required
def editar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, pk=espacio_id)
    
    if request.method == "POST":
        espacio.nombre = request.POST.get('nombre')
        espacio.ubicacion = request.POST.get('ubicacion')
        espacio.capacidad = request.POST.get('capacidad')
        # Checkbox en HTML no envía nada si no está marcado, por eso se usa 'in request.POST'
        espacio.activo = 'activo' in request.POST 
        
        if 'imagen' in request.FILES:
            espacio.imagen = request.FILES['imagen']
            
        espacio.save()
        messages.success(request, "Espacio actualizado correctamente.")
        return redirect("inventario:gestion_espacios")
        
    return render(request, "inventario/editar_espacio.html", {"espacio": espacio})

@admin_required
def eliminar_espacio(request, espacio_id):
    """
    Esta función NO borra el espacio físico para mantener el historial.
    1. Cancela reservas futuras.
    2. Desactiva el espacio (Soft Delete).
    """
    # IMPORTACIÓN AQUÍ DENTRO para evitar error circular con core/reservas
    from reservas.models import Reserva 
    
    espacio = get_object_or_404(Espacio, pk=espacio_id)
    
    # 1. Buscar reservas futuras activas que se verán afectadas
    hoy = timezone.now().date()
    reservas_afectadas = Reserva.objects.filter(
        espacio=espacio,
        fecha__gte=hoy,
        estado__in=['PENDIENTE', 'APROBADA']
    )
    
    cantidad_afectados = reservas_afectadas.count()
    
    msg_detalle = ""
    if cantidad_afectados > 0:
        # 2. Cancelar masivamente
        motivo = f"Cancelación automática: El espacio '{espacio.nombre}' ha sido eliminado/clausurado del inventario."
        
        reservas_afectadas.update(
            estado='CANCELADA', 
            motivo_cancelacion=motivo
        )
        msg_detalle = f" Se cancelaron {cantidad_afectados} reservas futuras automáticamente."
    else:
        msg_detalle = " No habían reservas futuras afectadas."

    # 3. Desactivar (Soft Delete)
    espacio.activo = False
    espacio.save()

    messages.warning(request, f"El espacio '{espacio.nombre}' ha sido DESACTIVADO.{msg_detalle}")
        
    return redirect("inventario:gestion_espacios")


# ==============================================================================
# GESTIÓN DE RECURSOS
# ==============================================================================

@admin_required
def gestion_recursos(request):

    def recurso_tiene_area() -> bool:
        try:
            return any(getattr(f, "name", None) == "area" for f in Recurso._meta.get_fields())
        except Exception:
            return False

    if request.method == "POST":
        codigo = request.POST.get('codigo')
        nombre = request.POST.get('nombre')
        stock = request.POST.get('stock')
        descripcion = request.POST.get('descripcion')

        try:
            # ✅ Creamos kwargs seguros (sin 'area' si tu modelo no lo tiene)
            create_kwargs = {
                "codigo": codigo,
                "nombre": nombre,
                "stock": stock,
                "descripcion": descripcion,
            }

            # (Opcional futuro) si algún día agregas area a Recurso
            if recurso_tiene_area() and getattr(request.user, "area_id", None):
                create_kwargs["area"] = request.user.area

            Recurso.objects.create(**create_kwargs)

            messages.success(request, "Recurso creado correctamente.")
            return redirect("inventario:gestion_recursos")

        except Exception as e:
            messages.error(request, f"Error al crear recurso: {e}")

    # ✅ Listado seguro (sin romper por campo 'area' inexistente)
    if request.user.is_superuser:
        recursos = Recurso.objects.all().order_by('nombre')
    else:
        # si existe area en el modelo, filtra; si no existe, muestra todo
        if recurso_tiene_area() and getattr(request.user, "area_id", None):
            recursos = Recurso.objects.filter(area=request.user.area).order_by('nombre')
        else:
            recursos = Recurso.objects.all().order_by('nombre')

    return render(request, "inventario/recursos.html", {"recursos": recursos})

@admin_required
def editar_recurso(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    
    if request.method == "POST":
        recurso.codigo = request.POST.get('codigo') # Permitimos editar código
        recurso.nombre = request.POST.get('nombre')
        recurso.stock = request.POST.get('stock')
        recurso.descripcion = request.POST.get('descripcion')
        recurso.save()
        
        messages.success(request, "Recurso actualizado.")
        return redirect("inventario:gestion_recursos")
        
    return render(request, "inventario/editar_recurso.html", {"recurso": recurso})

@admin_required
def eliminar_recurso(request, recurso_id):
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    try:
        recurso.delete()
        messages.success(request, f"Recurso '{recurso.nombre}' eliminado.")
    except ProtectedError:
        # Esto evita el pantallazo de error si el recurso está en uso
        messages.error(request, f"No se puede eliminar '{recurso.nombre}' porque está asociado a reservas existentes.")
    
    return redirect("inventario:gestion_recursos")