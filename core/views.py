from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout, login
from .models import CustomUser, Producto, Asignacion, CarritoItem, Venta
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.db.models import Count, Q, Sum, F, Case, When, Value
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .forms import CustomLoginForm, AsignacionForm, UserCreationFormWithRol, ProductoForm
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
import csv

@login_required
def gestionar_productos_view(request):
    """Vista para gestionar productos. Solo accesible para administradores."""
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        raise PermissionDenied("No tienes permiso para acceder a esta página.")
    
    productos = Producto.objects.all().order_by('-id')
    return render(request, 'core/gestionar_productos.html', {'productos': productos})

@login_required
def crear_producto_view(request):
    """Vista para crear nuevos productos."""
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        raise PermissionDenied("No tienes permiso para acceder a esta página.")
    
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto creado exitosamente.')
            return redirect('core:gestionar_productos')
    else:
        form = ProductoForm()
    
    return render(request, 'core/crear_producto.html', {'form': form})

@login_required
def editar_producto_view(request, producto_id):
    """Vista para editar productos existentes."""
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        raise PermissionDenied("No tienes permiso para acceder a esta página.")
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado exitosamente.')
            return redirect('core:gestionar_productos')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'core/editar_producto.html', {'form': form, 'producto': producto})

def home_view(request):
    """Vista de la página principal."""
    # Mostrar solo productos no exclusivos en la tienda normal
    productos = Producto.objects.filter(es_exclusivo=False)
    return render(request, 'core/home.html', {'productos': productos})

class CustomLoginView(LoginView):
    """Vista personalizada para el login."""
    template_name = 'core/login.html'
    form_class = CustomLoginForm

class CustomLogoutView(LogoutView):
    """Vista personalizada para el logout."""
    next_page = 'core:home'

@login_required
def asignar_view(request):
    """Vista para asignar roles."""
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        raise PermissionDenied("No tienes permiso para acceder a esta página.")
    
    asignaciones = Asignacion.objects.all()
    return render(request, 'core/asignar.html', {'asignaciones': asignaciones})

@login_required
def distribuidor_view(request):
    """Vista del panel de distribuidor."""
    if request.user.rol != 'DISTRIBUIDOR':
        raise PermissionDenied("No tienes permiso para acceder a esta página.")
    
    return render(request, 'core/distribuidor.html')

@login_required
def asignar_distribuidor_view(request):
    """Vista para asignar distribuidores."""
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        raise PermissionDenied("No tienes permiso para acceder a esta página.")
    
    return render(request, 'core/asignar_distribuidor.html')

@login_required
def revendedor_view(request):
    """Vista del panel de revendedor."""
    if request.user.rol != 'REVENDEDOR':
        raise PermissionDenied("No tienes permiso para acceder a esta página.")
    
    return render(request, 'core/revendedor.html')

@login_required
def carrito_view(request, producto_id=None):
    """Vista del carrito de compras."""
    if producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
        CarritoItem.objects.create(
            usuario=request.user,
            producto=producto,
            cantidad=1
        )
        messages.success(request, 'Producto agregado al carrito.')
        return redirect('core:carrito')
    
    items = CarritoItem.objects.filter(usuario=request.user)
    return render(request, 'core/carrito.html', {'items': items})

@login_required
def eliminar_carrito_item(request, item_id):
    """Vista para eliminar items del carrito."""
    item = get_object_or_404(CarritoItem, id=item_id, usuario=request.user)
    item.delete()
    messages.success(request, 'Producto eliminado del carrito.')
    return redirect('core:carrito')

@login_required
def checkout_view(request):
    """Vista del proceso de checkout."""
    return render(request, 'core/checkout.html')

@login_required
def checkout_exclusivo_view(request):
    """Vista del proceso de checkout exclusivo."""
    return render(request, 'core/checkout_exclusivo.html')

@login_required
def procesar_pago(request):
    """Vista para procesar pagos."""
    # Lógica de procesamiento de pago
    return redirect('core:home')

@login_required
def pago_transferencia_view(request):
    """Vista para pagos por transferencia."""
    return render(request, 'core/pago_transferencia.html')

def registro_rapido(request):
    """Vista para registro rápido de usuarios."""
    if request.method == 'POST':
        form = UserCreationFormWithRol(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro exitoso.')
            return redirect('core:home')
    else:
        form = UserCreationFormWithRol()
    return render(request, 'core/registro_rapido.html', {'form': form})

@login_required
def procesar_compra_carrito(request):
    """Vista para procesar compras del carrito."""
    # Lógica de procesamiento de compra
    return redirect('core:home')

def register_user(request):
    """Vista para registro de usuarios."""
    if request.method == 'POST':
        form = UserCreationFormWithRol(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registro exitoso.')
            return redirect('core:home')
    else:
        form = UserCreationFormWithRol()
    return render(request, 'core/register.html', {'form': form})

@login_required
def cambiar_estado_asignacion(request, asignacion_id):
    """Vista para cambiar estado de asignaciones."""
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        raise PermissionDenied("No tienes permiso para realizar esta acción.")
    
    asignacion = get_object_or_404(Asignacion, id=asignacion_id)
    asignacion.estado = not asignacion.estado
    asignacion.save()
    return redirect('core:asignar')

@login_required
def tienda_oculta_view(request):
    """Vista de la tienda oculta."""
    # Mostrar solo productos exclusivos en la tienda oculta
    productos = Producto.objects.filter(es_exclusivo=True)
    return render(request, 'core/tienda_oculta.html', {'productos': productos})

def contact_view(request):
    """Vista de contacto."""
    return render(request, 'core/contact.html')
