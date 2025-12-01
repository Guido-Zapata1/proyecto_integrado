from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Espacio, Recurso

# ==============================================================================
# GESTIÓN DE ESPACIOS
# ==============================================================================

@login_required
def gestion_espacios(request):
    if request.method == "POST":
        nombre = request.POST.get('nombre')
        ubicacion = request.POST.get('ubicacion')
        capacidad = request.POST.get('capacidad')
        
        # Capturamos la imagen (si se subió alguna)
        imagen = request.FILES.get('imagen') 

        try:
            Espacio.objects.create(
                nombre=nombre,
                ubicacion=ubicacion,
                capacidad=capacidad,
                imagen=imagen # Guardamos la imagen
            )
            messages.success(request, "Espacio creado correctamente.")
            return redirect("gestion_espacios")
        except Exception as e:
            messages.error(request, f"Error al crear espacio: {e}")

    espacios = Espacio.objects.all().order_by('nombre')
    return render(request, "inventario/espacios.html", {"espacios": espacios})

@login_required
def editar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, pk=espacio_id)
    
    if request.method == "POST":
        espacio.nombre = request.POST.get('nombre')
        espacio.ubicacion = request.POST.get('ubicacion')
        espacio.capacidad = request.POST.get('capacidad')
        espacio.activo = 'activo' in request.POST
        
        # Si se sube una nueva imagen, reemplazamos la anterior
        if 'imagen' in request.FILES:
            espacio.imagen = request.FILES['imagen']
            
        espacio.save()
        messages.success(request, "Espacio actualizado correctamente.")
        return redirect("gestion_espacios")
        
    return render(request, "inventario/editar_espacio.html", {"espacio": espacio})

@login_required
def eliminar_espacio(request, espacio_id):
    espacio = get_object_or_404(Espacio, pk=espacio_id)
    espacio.delete()
    messages.success(request, "Espacio eliminado.")
    return redirect("gestion_espacios")

# ... (El resto de tus vistas de Recursos se mantienen igual) ...
@login_required
def gestion_recursos(request):
    # (Mantén tu código de recursos aquí si lo tenías separado, o usa el de core)
    pass


@login_required
def eliminar_espacio(request, espacio_id):
    """Elimina un espacio específico."""
    espacio = get_object_or_404(Espacio, pk=espacio_id)
    nombre = espacio.nombre
    espacio.delete()
    messages.warning(request, f"Espacio '{nombre}' eliminado.")
    return redirect("gestion_espacios")


@login_required
def editar_espacio(request, espacio_id):
    """
    Busca un espacio, carga sus datos en el formulario y guarda los cambios.
    """
    espacio = get_object_or_404(Espacio, pk=espacio_id)
    
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            capacidad = request.POST.get("capacidad")
            ubicacion = request.POST.get("ubicacion")
            # El checkbox HTML envía 'on' si está marcado, o nada si no.
            activo = request.POST.get("activo") == "on"

            if not nombre or not capacidad:
                messages.error(request, "Nombre y Capacidad son obligatorios.")
            else:
                # Actualizamos los datos del objeto
                espacio.nombre = nombre
                espacio.capacidad = capacidad
                espacio.ubicacion = ubicacion
                espacio.activo = activo
                espacio.save() # Guardamos en la BD
                
                messages.success(request, f"Espacio '{nombre}' actualizado correctamente.")
                return redirect("gestion_espacios")

        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")

    # Si es GET, mostramos el formulario con los datos actuales del espacio
    return render(request, "inventario/editar_espacio.html", {"espacio": espacio})


# ==============================================================================
# GESTIÓN DE RECURSOS
# ==============================================================================

@login_required
def gestion_recursos(request):
    """
    Vista unificada: Muestra la lista de recursos y procesa la creación de nuevos.
    """
    # 1. PROCESAR CREACIÓN (POST)
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            # Recibimos 'cantidad' del HTML y lo guardamos en 'stock' del modelo
            cantidad = request.POST.get("cantidad")
            descripcion = request.POST.get("descripcion")

            if not nombre or not cantidad:
                messages.error(request, "Nombre y Cantidad son obligatorios.")
            else:
                Recurso.objects.create(
                    nombre=nombre,
                    stock=cantidad, 
                    descripcion=descripcion
                )
                messages.success(request, f"Recurso '{nombre}' creado correctamente.")
                return redirect("gestion_recursos")

        except Exception as e:
            messages.error(request, f"Error al crear recurso: {e}")

    # 2. MOSTRAR LISTA (GET)
    recursos = Recurso.objects.all().order_by('nombre')
    return render(request, "inventario/recursos.html", {"recursos": recursos})


@login_required
def eliminar_recurso(request, recurso_id):
    """Elimina un recurso específico."""
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    nombre = recurso.nombre
    recurso.delete()
    messages.warning(request, f"Recurso '{nombre}' eliminado.")
    return redirect("gestion_recursos")


@login_required
def editar_recurso(request, recurso_id):
    """
    Busca un recurso, carga sus datos en el formulario y guarda los cambios.
    """
    recurso = get_object_or_404(Recurso, pk=recurso_id)
    
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            cantidad = request.POST.get("cantidad")
            descripcion = request.POST.get("descripcion")

            if not nombre or not cantidad:
                messages.error(request, "Nombre y Cantidad son obligatorios.")
            else:
                # Actualizamos los datos del objeto
                recurso.nombre = nombre
                recurso.stock = cantidad
                recurso.descripcion = descripcion
                recurso.save() # Guardamos en la BD
                
                messages.success(request, f"Recurso '{nombre}' actualizado correctamente.")
                return redirect("gestion_recursos")

        except Exception as e:
            messages.error(request, f"Error al actualizar: {e}")

    # Si es GET, mostramos el formulario con los datos actuales del recurso
    return render(request, "inventario/editar_recurso.html", {"recurso": recurso})
