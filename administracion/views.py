from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import get_user_model
from core.forms import CustomUserCreationForm
from inventario.models import Recurso, Espacio
from django.contrib import messages  # ← IMPORTA TUS MODELOS
from openpyxl import Workbook
from django.http import HttpResponse
from reservas.models import Reserva
User = get_user_model()

# ==============================
# DASHBOARD PRINCIPAL
# ==============================
def admin_dashboard(request):
    return render(request, 'administracion/dashboard.html')


# ==============================
# LISTA DE USUARIOS + BUSCADOR
# ==============================
def gestion_usuarios(request):

    filtro = request.GET.get("filtro", "")
    rol = request.GET.get("rol", "")

    usuarios = User.objects.all()

    if filtro:
        usuarios = usuarios.filter(
            last_name__icontains=filtro
        ) | usuarios.filter(
            first_name__icontains=filtro
        ) | usuarios.filter(
            email__icontains=filtro
        )

    if rol:
        usuarios = usuarios.filter(rol=rol)

    context = {
        "users": usuarios,
        "filtro": filtro,
        "rol": rol,
        "roles": User.ROLES,
    }

    return render(request, 'administracion/gestion_usuarios.html', context)


# ==============================
# CREAR USUARIO
# ==============================
def crear_usuario(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)

        # Convertimos los nombres de tu HTML a los que espera el form
        form.data = form.data.copy()
        form.data["password1"] = request.POST.get("password")
        form.data["password2"] = request.POST.get("confirm_password")

        if form.is_valid():
            form.save()
            messages.success(request, "Usuario creado correctamente.")
            return redirect("administracion:lista_usuarios")
        else:
            print("ERRORES DEL FORMULARIO:", form.errors)
        messages.error(request, f"Errores: {form.errors}")
    else:
        form = CustomUserCreationForm()

    return render(request, "administracion/crear_usuarios.html", {"form": form})


# ==============================
# EDITAR ROL DE USUARIO
# ==============================
def editar_rol_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        nuevo_rol = request.POST.get("rol")
        if nuevo_rol in dict(User.ROLES).keys():
            usuario.rol = nuevo_rol
            usuario.save()
            return redirect("administracion:lista_usuarios")

    context = {
        "usuario": usuario,
        "roles": User.ROLES,
    }

    return render(request, "administracion/editar_rol.html", context)


# ==============================
# ACTIVAR / DESACTIVAR USUARIO
# ==============================
def gestionar_rol_estado(request, user_id):
    user = get_object_or_404(User, id=user_id)

    action = request.POST.get("action")
    value = request.POST.get("value")

    if action == "rol":
        user.rol = value
        user.save()

    elif action == "toggle_active":
        user.is_active = not user.is_active
        user.save()

    return redirect("administracion:lista_usuarios")


# ==============================
# CRUD — RECURSOS (ANTES INVENTARIO)
# ==============================
def gestion_recursos(request):
    recursos = Recurso.objects.all()
    return render(request, "administracion/recursos.html", {"recursos": recursos})


def crear_recurso(request):
    if request.method == "POST":
        nombre = request.POST["nombre"]
        cantidad = request.POST["cantidad"]
        descripcion = request.POST.get("descripcion", "")

        Recurso.objects.create(
            nombre=nombre,
            cantidad=cantidad,
            descripcion=descripcion
        )
        return redirect("recursos:gestion")

    return redirect("recursos:gestion")


def eliminar_recurso(request, id):
    recurso = get_object_or_404(Recurso, id=id)
    recurso.delete()
    return redirect("recursos:gestion")


# ==============================
# CRUD — ESPACIOS
# ==============================
def lista_espacios(request):
    espacios = Espacio.objects.all()
    return render(request, "administracion/espacios.html", {"espacios": espacios})


def crear_espacio(request):
    if request.method == "POST":
        nombre = request.POST["nombre"]
        capacidad = request.POST["capacidad"]
        descripcion = request.POST.get("descripcion", "")

        Espacio.objects.create(
            nombre=nombre,
            capacidad=capacidad,
            descripcion=descripcion
        )
        return redirect("administracion:lista_espacios")

    return redirect("administracion:lista_espacios")


def eliminar_espacio(request, id):
    espacio = get_object_or_404(Espacio, id=id)
    espacio.delete()
    return redirect("administracion:lista_espacios")


def export_reservas_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Reservas"

    # Encabezados
    ws.append(["ID", "Usuario", "Espacio", "Fecha Inicio", "Fecha Fin", "Estado"])

    # Datos
    reservas = Reserva.objects.all()
    for r in reservas:
        ws.append([
            r.id,
            str(r.usuario),
            str(r.espacio),
            r.fecha_inicio,
            r.fecha_fin,
            r.estado
        ])

    # Respuesta HTTP
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="reservas.xlsx"'
    wb.save(response)
    return response
