from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout, login
from .models import CustomUser, Producto, Asignacion, CarritoItem, Venta
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Count, Q
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .forms import CustomLoginForm, AsignacionForm, UserCreationFormWithRol, ProductoForm
from .models import Producto, Asignacion, CarritoItem, Venta
from decimal import Decimal
from django.http import JsonResponse

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    authentication_form = CustomLoginForm
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'core:home'

def home_view(request):
    productos = Producto.objects.all()
    print(f"Cantidad de productos en DB: {productos.count()}")
    return render(request, 'core/home.html', {'productos': productos})

@login_required
def asignar_view(request):
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")
    
    if request.method == 'POST':
        form = AsignacionForm(request.POST, user=request.user)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.admin = request.user
            asignacion.save()
            messages.success(request, 'Asignación creada correctamente.')
            return redirect('core:asignar')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AsignacionForm(user=request.user)
    
    asignaciones = Asignacion.objects.all().order_by('-fecha_asignacion')

    # Calcular datos de ventas para la pestaña "Ventas"
    total_ventas = 0
    cantidad_vendida = 0
    costo_total = 0
    ganancia = 0

    ventas = Asignacion.objects.filter(estado='PAGADO')
    for venta in ventas:
        cantidad_vendida += venta.cantidad
        costo_total += venta.producto.costo * venta.cantidad
        total_ventas += venta.producto.precio * venta.cantidad

    ganancia = total_ventas - costo_total

    # Calcular estadísticas de ventas web
    from django.db.models import Sum, Count, F
    from django.utils import timezone
    from datetime import timedelta
    
    hoy = timezone.now()
    mes_actual = hoy.month
    mes_anterior = (hoy - timedelta(days=30)).month
    
    ventas_web = Venta.objects.filter(comprador__isnull=True) | Venta.objects.filter(comprador__rol='CLIENTE')
    ventas_web_mes = ventas_web.filter(fecha_venta__month=mes_actual)
    ventas_web_mes_anterior = ventas_web.filter(fecha_venta__month=mes_anterior)
    
    total_ventas_web = ventas_web_mes.aggregate(total=Sum('total', default=0))['total']
    total_ventas_anterior = ventas_web_mes_anterior.aggregate(total=Sum('total', default=0))['total'] or 1
    
    porcentaje_cambio_ventas = ((total_ventas_web - total_ventas_anterior) / total_ventas_anterior) * 100
    
    costos_totales_web = ventas_web_mes.aggregate(
        costos=Sum(F('producto__costo') * F('cantidad'), default=0)
    )['costos']
    
    ganancias_netas_web = total_ventas_web - costos_totales_web
    porcentaje_costos = (costos_totales_web / total_ventas_web * 100) if total_ventas_web else 0
    margen_ganancia = (ganancias_netas_web / total_ventas_web * 100) if total_ventas_web else 0
    
    total_clientes = ventas_web.values('email_comprador').distinct().count()
    clientes_registrados = ventas_web.filter(comprador__isnull=False).values('comprador').distinct().count()
    porcentaje_clientes_registrados = (clientes_registrados / total_clientes * 100) if total_clientes else 0

    # Set panel title based on user role
    panel_title = "Mi Panel" if request.user.rol == 'ADMIN' else "Panel de Administración"
    
    # --- FINANZAS CALCULATIONS ---
    # Combine metrics from both assignment sales and web sales
    overall_total_sales = total_ventas + (total_ventas_web or 0)
    overall_total_cost = costo_total + (costos_totales_web or 0)
    overall_profit = ganancia + (ganancias_netas_web or 0)
    
    # Calculate percentages safely
    if overall_total_sales > 0:
        overall_cost_percent = (overall_total_cost / overall_total_sales) * 100
        overall_profit_margin = (overall_profit / overall_total_sales) * 100
    else:
        overall_cost_percent = 0
        overall_profit_margin = 0
    
    context = {
        'form': form,
        'asignaciones': asignaciones,
        'total_ventas': total_ventas,
        'cantidad_vendida': cantidad_vendida,
        'costo_total': costo_total,
        'ganancia': ganancia,
        'panel_title': panel_title,
        # Datos de ventas web
        'ventas_web': ventas_web.order_by('-fecha_venta'),
        'total_ventas_web': total_ventas_web,
        'porcentaje_cambio_ventas': porcentaje_cambio_ventas,
        'costos_totales_web': costos_totales_web,
        'ganancias_netas_web': ganancias_netas_web,
        'porcentaje_costos': porcentaje_costos,
        'margen_ganancia': margen_ganancia,
        'total_clientes': total_clientes,
        'porcentaje_clientes_registrados': porcentaje_clientes_registrados,
        # Datos consolidados para la pestaña Finanzas
        'finanzas_total_sales': overall_total_sales,
        'finanzas_total_cost': overall_total_cost,
        'finanzas_total_profit': overall_profit,
        'finanzas_cost_percent': overall_cost_percent,
        'finanzas_profit_margin': overall_profit_margin,
    }

    return render(request, 'core/asignar.html', context)

@login_required
def distribuidor_view(request):
    if request.user.rol != 'DISTRIBUIDOR':
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")
    
    if request.method == 'POST':
        form = AsignacionForm(request.POST, user=request.user)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.admin = request.user
            asignacion.save()
            messages.success(request, 'Asignación creada correctamente.')
            return redirect('core:distribuidor')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AsignacionForm(user=request.user)
    
    # Filtrar asignaciones propias y las que ha creado
    asignaciones_propias = Asignacion.objects.filter(distribuidor=request.user).order_by('-fecha_asignacion')
    asignaciones_creadas = Asignacion.objects.filter(admin=request.user).order_by('-fecha_asignacion')
    
    productos_distintos = Asignacion.objects.filter(distribuidor=request.user).aggregate(
        total=Count('producto', distinct=True)
    )['total']
    
    return render(request, 'core/distribuidor.html', {
        'form': form,
        'asignaciones_propias': asignaciones_propias,
        'asignaciones_creadas': asignaciones_creadas,
        'productos_distintos': productos_distintos
    })

def carrito_view(request, producto_id=None):
    if producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
        # Agregar producto al carrito
        if request.method == 'POST':
            cantidad = int(request.POST.get('cantidad', 1))
            if not request.session.session_key:
                request.session.create()
            
            CarritoItem.objects.create(
                producto=producto,
                cantidad=cantidad,
                session_key=request.session.session_key
            )
            messages.success(request, 'Producto agregado al carrito.')
            return redirect('core:carrito')
        
        return render(request, 'core/agregar_carrito.html', {'producto': producto})
    
    # Vista del carrito
    if not request.session.session_key:
        request.session.create()
    
    items = CarritoItem.objects.filter(session_key=request.session.session_key)
    total = sum(item.producto.precio * item.cantidad for item in items)
    
    return render(request, 'core/carrito.html', {
        'items': items,
        'total': total
    })

def eliminar_carrito_item(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        item = get_object_or_404(CarritoItem, id=item_id, session_key=request.session.session_key)
        item.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def procesar_compra_carrito(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        if not request.session.session_key:
            return JsonResponse({'error': 'No hay sesión activa'}, status=400)
        
        items = CarritoItem.objects.filter(session_key=request.session.session_key)
        if not items:
            return JsonResponse({'error': 'El carrito está vacío'}, status=400)
        
        email = request.POST.get('email', '')
        total_venta = Decimal('0')
        ventas = []

        for item in items:
            subtotal = item.producto.precio * item.cantidad
            total_venta += subtotal
            
            venta = Venta.objects.create(
                producto=item.producto,
                cantidad=item.cantidad,
                total=subtotal,
                email_comprador=email
            )
            ventas.append(venta.id)
        
        # Limpiar el carrito
        items.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Compra procesada correctamente',
            'ventas': ventas,
            'total': str(total_venta)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def cambiar_estado_asignacion(request, asignacion_id):
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tiene permiso para cambiar el estado.")
    
    asignacion = get_object_or_404(Asignacion, id=asignacion_id)
    asignacion.estado = 'PAGADO' if asignacion.estado == 'PENDIENTE' else 'PENDIENTE'
    asignacion.save()
    
    messages.success(request, f'Estado actualizado a {asignacion.get_estado_display()}')
    return redirect('core:asignar')

@login_required
def editar_producto(request, producto_id):
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tiene permiso para editar productos.")
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producto actualizado correctamente.')
            return redirect('core:home')
    else:
        form = ProductoForm(instance=producto)
    
    return render(request, 'core/editar_producto.html', {'form': form})

@login_required
def revendedor_view(request):
    if request.user.rol != 'REVENDEDOR':
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")
    
    asignaciones = Asignacion.objects.filter(distribuidor=request.user).order_by('-fecha_asignacion')
    return render(request, 'core/revendedor.html', {
        'asignaciones': asignaciones
    })

def register_user(request):
    if not request.user.is_authenticated:
        return redirect('core:login')
        
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO', 'DISTRIBUIDOR']:
        return HttpResponseForbidden("No tiene permiso para registrar usuarios.")
        
    if request.method == 'POST':
        form = UserCreationFormWithRol(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuario creado exitosamente.')
            return redirect('core:asignar')
    else:
        form = UserCreationFormWithRol(user=request.user)
    
    return render(request, 'core/register.html', {'form': form})

def registro_rapido(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        nombre = request.POST.get('nombre')
        email = request.POST.get('email')
        dni = request.POST.get('dni')
        domicilio = request.POST.get('domicilio')
        
        try:
            # Crear usuario con rol CLIENTE por defecto
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                nombre=nombre,
                dni=dni,
                domicilio=domicilio,
                rol='CLIENTE'
            )
            
            # Iniciar sesión automáticamente
            login(request, user)
            
            messages.success(request, '¡Cuenta creada exitosamente! Bienvenido/a.')
            return redirect('core:home')
            
        except Exception as e:
            messages.error(request, f'Error al crear la cuenta: {str(e)}')
            return redirect('core:checkout')
    else:
        # GET: mostrar formulario con datos pre-llenados
        context = {
            'nombre': request.GET.get('nombre', ''),
            'email': request.GET.get('email', ''),
            'dni': request.GET.get('dni', ''),
            'domicilio': request.GET.get('domicilio', '')
        }
        return render(request, 'core/registro_rapido.html', context)

def checkout_view(request):
    if not request.session.session_key:
        request.session.create()
    
    items = CarritoItem.objects.filter(session_key=request.session.session_key)
    if not items:
        messages.warning(request, 'Tu carrito está vacío.')
        return redirect('core:carrito')
    
    total = sum(item.producto.precio * item.cantidad for item in items)
    
    return render(request, 'core/checkout.html', {
        'items': items,
        'total': total
    })

@login_required
def ventas_web_view(request):
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")
    
    from django.db.models import Q, Sum, Count, F
    from django.utils import timezone
    from datetime import timedelta
    
    hoy = timezone.now()
    mes_actual = hoy.month
    mes_anterior = (hoy - timedelta(days=30)).month
    
    # Filtrar solo ventas web (sin comprador o comprador con rol CLIENTE)
    ventas = Venta.objects.filter(
        Q(comprador__isnull=True) | Q(comprador__rol='CLIENTE')
    )
    ventas_mes_actual = ventas.filter(fecha_venta__month=mes_actual)
    ventas_mes_anterior = ventas.filter(fecha_venta__month=mes_anterior)
    
    total_ventas = ventas_mes_actual.aggregate(
        total=Sum('total', default=0)
    )['total'] or 0
    
    total_ventas_anterior = ventas_mes_anterior.aggregate(
        total=Sum('total', default=0)
    )['total'] or 1  # Evitar división por cero
    
    porcentaje_cambio_ventas = ((total_ventas - total_ventas_anterior) / total_ventas_anterior) * 100
    
    # Calcular costos y ganancias
    costos_totales = ventas_mes_actual.aggregate(
        costos=Sum(F('producto__costo') * F('cantidad'), default=0)
    )['costos'] or 0
    
    ganancias_netas = total_ventas - costos_totales
    porcentaje_costos = (costos_totales / total_ventas * 100) if total_ventas else 0
    margen_ganancia = (ganancias_netas / total_ventas * 100) if total_ventas else 0
    
    # Estadísticas de clientes
    total_clientes = ventas.values('email_comprador').distinct().count()
    clientes_registrados = ventas.filter(comprador__isnull=False).values('comprador').distinct().count()
    porcentaje_clientes_registrados = (clientes_registrados / total_clientes * 100) if total_clientes else 0
    
    clientes_nuevos = ventas_mes_actual.values('email_comprador').distinct().count()
    porcentaje_clientes_nuevos = (clientes_nuevos / total_clientes * 100) if total_clientes else 0
    
    # Productos más vendidos
    productos_top = ventas_mes_actual.values(
        'producto__nombre'
    ).annotate(
        nombre=F('producto__nombre'),
        unidades=Sum('cantidad'),
        ingresos=Sum('total')
    ).order_by('-unidades')[:5]
    
    # Tasa de conversión (clientes que completaron la compra)
    total_visitas = CarritoItem.objects.values('session_key').distinct().count() or 1
    tasa_conversion = (ventas.count() / total_visitas) * 100
    
    context = {
        'ventas': ventas.order_by('-fecha_venta'),
        'total_ventas': total_ventas,
        'porcentaje_cambio_ventas': porcentaje_cambio_ventas,
        'costos_totales': costos_totales,
        'ganancias_netas': ganancias_netas,
        'porcentaje_costos': porcentaje_costos,
        'margen_ganancia': margen_ganancia,
        'total_clientes': total_clientes,
        'porcentaje_clientes_registrados': porcentaje_clientes_registrados,
        'clientes_nuevos': clientes_nuevos,
        'porcentaje_clientes_nuevos': porcentaje_clientes_nuevos,
        'productos_top': productos_top,
        'tasa_conversion': tasa_conversion,
    }
    
    return render(request, 'core/ventas_web.html', context)

def procesar_pago(request):
    if request.method != 'POST':
        return redirect('core:checkout')
    
    try:
        if not request.session.session_key:
            messages.error(request, 'No hay sesión activa.')
            return redirect('core:carrito')
        
        items = CarritoItem.objects.filter(session_key=request.session.session_key)
        if not items:
            messages.error(request, 'El carrito está vacío.')
            return redirect('core:carrito')
        
        # Obtener datos del formulario
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '').strip()
        dni = request.POST.get('dni', '').strip()
        domicilio = request.POST.get('domicilio', '').strip()
        
        # Validar campos obligatorios
        if not all([nombre, email, dni, domicilio]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return redirect('core:checkout')
        
        # Validar DNI
        if not dni.isdigit() or len(dni) < 7 or len(dni) > 8:
            messages.error(request, 'El DNI debe tener entre 7 y 8 dígitos.')
            return redirect('core:checkout')
        
        # Actualizar datos del usuario si está autenticado
        comprador = None
        if request.user.is_authenticated:
            user = request.user
            user.nombre = nombre
            user.email = email
            user.dni = dni
            user.domicilio = domicilio
            user.save()
            comprador = user
        
        total_venta = Decimal('0')
        ventas = []

        # Crear las ventas
        for item in items:
            subtotal = item.producto.precio * item.cantidad
            total_venta += subtotal
            
            venta = Venta.objects.create(
                producto=item.producto,
                cantidad=item.cantidad,
                total=subtotal,
                email_comprador=email,
                nombre_comprador=nombre,
                comprador=comprador,
                estado_pago='PAGADO'  # Asumimos que el pago es exitoso
            )
            ventas.append(venta.id)
        
        # Limpiar el carrito
        items.delete()
        
        messages.success(request, f'¡Compra procesada correctamente! Total: ${total_venta} ARS. IDs de venta: {", ".join(map(str, ventas))}')
        return redirect('core:home')
        
    except Exception as e:
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('core:checkout')
