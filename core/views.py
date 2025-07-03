from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout, login
from .models import CustomUser, Producto, Asignacion, CarritoItem, Venta
from django.http import HttpResponseForbidden
from django.contrib import messages
from django.db.models import Count, Q, Sum, F, Case, When, Value
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from .forms import StockForm, AsignacionForm, UserCreationFormWithRol
from django.contrib.auth.forms import AuthenticationForm

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'core:home'
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    authentication_form = AuthenticationForm
    redirect_authenticated_user = True

class CustomLogoutView(LogoutView):
    next_page = 'core:home'

def home_view(request):
    productos_salud = Producto.objects.filter(es_exclusivo=False, categoria='SALUD')
    productos_belleza = Producto.objects.filter(es_exclusivo=False, categoria='BELLEZA')
    productos_higiene = Producto.objects.filter(es_exclusivo=False, categoria='HIGIENE')
    context = {
        'productos_salud': productos_salud,
        'productos_belleza': productos_belleza,
        'productos_higiene': productos_higiene,
    }
    return render(request, 'core/home.html', context)

@login_required
def tienda_oculta_view(request):
    """Vista para la tienda oculta, solo accesible para usuarios registrados"""
    productos_exclusivos = Producto.objects.filter(es_exclusivo=True)
    return render(request, 'core/tienda_oculta.html', {'productos_exclusivos': productos_exclusivos})

@login_required
def gestionar_productos_view(request):
    """Vista para gestionar productos"""
    # Verificar que el usuario sea admin o superusuario
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return redirect('core:home')
    
    productos = Producto.objects.all().order_by('nombre')
    return render(request, 'core/gestionar_productos.html', {'productos': productos})

@login_required
def editar_producto_view(request, producto_id):
    """Vista para editar un producto"""
    # Verificar que el usuario sea admin o superusuario
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return redirect('core:home')
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        # Actualizar los campos básicos
        producto.nombre = request.POST.get('nombre')
        producto.descripcion = request.POST.get('descripcion')
        producto.precio = request.POST.get('precio')
        producto.precio_distribuidor = request.POST.get('precio_distribuidor')
        producto.precio_revendedor = request.POST.get('precio_revendedor')
        producto.imagen_url = request.POST.get('imagen_url')
        producto.es_exclusivo = request.POST.get('es_exclusivo') == 'on'
        
        # Solo actualizar el costo si el usuario es admin o superusuario
        if request.user.rol in ['ADMIN', 'SUPERUSUARIO']:
            producto.costo = request.POST.get('costo')
        
        producto.save()
        return redirect('core:home')
    
    return render(request, 'core/editar_producto.html', {'producto': producto})

@login_required
def crear_producto_view(request):
    """Vista para crear un nuevo producto"""
    # Verificar que el usuario sea admin o superusuario
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return redirect('core:home')
    
    if request.method == 'POST':
        # Crear el producto con los datos del formulario
        producto = Producto(
            nombre=request.POST.get('nombre'),
            descripcion=request.POST.get('descripcion'),
            precio=request.POST.get('precio'),
            precio_distribuidor=request.POST.get('precio_distribuidor'),
            precio_revendedor=request.POST.get('precio_revendedor'),
            imagen_url=request.POST.get('imagen_url'),
            es_exclusivo=request.POST.get('es_exclusivo') == 'on',
            categoria=request.POST.get('categoria', 'SALUD'),  # Added categoria field with default
        )
        
        # Solo establecer el costo si el usuario es admin o superusuario
        if request.user.rol in ['ADMIN', 'SUPERUSUARIO']:
            producto.costo = request.POST.get('costo')
        
        producto.save()
        return redirect('core:gestionar_productos')
    
    return render(request, 'core/editar_producto.html', {'producto': None})

@login_required
def asignar_view(request):
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")
    
    if request.method == 'POST':
        form = AsignacionForm(request.POST, user=request.user)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.admin = request.user
            
            # Verificar que el distribuidor solo pueda asignar a revendedores
            if request.user.rol == 'DISTRIBUIDOR' and form.cleaned_data['distribuidor'].rol != 'REVENDEDOR':
                messages.error(request, 'Como distribuidor, solo puede asignar stock a revendedores.')
                return redirect('core:asignar')
            
            asignacion.save()
            messages.success(request, 'Asignación creada correctamente.')
            return redirect('core:asignar')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AsignacionForm(user=request.user)
    
    # Obtener las asignaciones para la pestaña "Asignaciones"
    asignaciones = Asignacion.objects.all().order_by('-fecha_asignacion')

    # Obtener métricas para la pestaña "Finanzas"
    hoy = timezone.now()
    mes_actual = hoy.month
    mes_anterior = (hoy - timedelta(days=30)).month
    
    # Ventas Web (todas las ventas para mostrar, pero solo pagadas para finanzas)
    ventas_web = Venta.objects.all()  # Todas las ventas para mostrar
    ventas_web_pagadas = ventas_web.filter(estado_pago='PAGADO')  # Solo pagadas para finanzas
    ventas_web_mes = ventas_web_pagadas.filter(fecha_venta__month=mes_actual)
    ventas_web_mes_anterior = ventas_web_pagadas.filter(fecha_venta__month=mes_anterior)
    
    total_ventas_web = ventas_web_mes.aggregate(total=Sum('total', default=0))['total'] or 0
    total_ventas_web_anterior = ventas_web_mes_anterior.aggregate(total=Sum('total', default=0))['total'] or 1
    
    # Ventas por Asignación
    asignaciones_pagadas = Asignacion.objects.filter(estado='PAGADO')
    asignaciones_mes = asignaciones_pagadas.filter(fecha_asignacion__month=mes_actual)
    asignaciones_mes_anterior = asignaciones_pagadas.filter(fecha_asignacion__month=mes_anterior)
    
    # Calcular totales usando Case para determinar el precio según el rol del distribuidor
    total_ventas_asignacion = asignaciones_mes.aggregate(
        total=Sum(
            Case(
                When(distribuidor__rol='DISTRIBUIDOR', then=F('producto__precio_distribuidor') * F('cantidad')),
                When(distribuidor__rol='REVENDEDOR', then=F('producto__precio_revendedor') * F('cantidad')),
                default=F('producto__precio') * F('cantidad'),
            ),
            default=0
        )
    )['total'] or 0
    
    total_ventas_asignacion_anterior = asignaciones_mes_anterior.aggregate(
        total=Sum(
            Case(
                When(distribuidor__rol='DISTRIBUIDOR', then=F('producto__precio_distribuidor') * F('cantidad')),
                When(distribuidor__rol='REVENDEDOR', then=F('producto__precio_revendedor') * F('cantidad')),
                default=F('producto__precio') * F('cantidad'),
            ),
            default=0
        )
    )['total'] or 1
    
    # Costos Web (solo de ventas pagadas)
    costos_web = ventas_web_mes.aggregate(
        costos=Sum(F('producto__costo') * F('cantidad'), default=0)
    )['costos'] or 0
    
    # Costos Asignaciones
    costos_asignacion = asignaciones_mes.aggregate(
        costos=Sum(F('producto__costo') * F('cantidad'), default=0)
    )['costos'] or 0
    
    # Métricas de Ventas Web
    ganancias_web = total_ventas_web - costos_web
    porcentaje_costos_web = (costos_web / total_ventas_web * 100) if total_ventas_web else 0
    margen_ganancia_web = (ganancias_web / total_ventas_web * 100) if total_ventas_web else 0
    
    # Métricas de Asignaciones
    ganancias_asignacion = total_ventas_asignacion - costos_asignacion
    porcentaje_costos_asignacion = (costos_asignacion / total_ventas_asignacion * 100) if total_ventas_asignacion else 0
    margen_ganancia_asignacion = (ganancias_asignacion / total_ventas_asignacion * 100) if total_ventas_asignacion else 0
    
    porcentaje_cambio_asignaciones = ((total_ventas_asignacion - total_ventas_asignacion_anterior) / total_ventas_asignacion_anterior * 100)
    
    # Métricas de Distribuidores
    total_distribuidores = CustomUser.objects.filter(rol='DISTRIBUIDOR').count()
    distribuidores_activos = Asignacion.objects.filter(
        fecha_asignacion__month=mes_actual
    ).values('distribuidor').distinct().count()
    
    porcentaje_distribuidores_activos = (distribuidores_activos / total_distribuidores * 100) if total_distribuidores else 0
    
    # Totales Combinados
    total_ventas = total_ventas_web + total_ventas_asignacion
    total_ventas_anterior = total_ventas_web_anterior + total_ventas_asignacion_anterior
    
    porcentaje_cambio_ventas = ((total_ventas - total_ventas_anterior) / total_ventas_anterior) * 100
    
    costos_totales = costos_web + costos_asignacion
    ganancias_netas = total_ventas - costos_totales
    
    porcentaje_costos = (costos_totales / total_ventas * 100) if total_ventas else 0
    margen_ganancia = (ganancias_netas / total_ventas * 100) if total_ventas else 0
    
    porcentaje_ventas_web = (total_ventas_web / total_ventas * 100) if total_ventas else 0
    porcentaje_ventas_asignacion = (total_ventas_asignacion / total_ventas * 100) if total_ventas else 0
    
    # Métricas de Clientes
    total_clientes = ventas_web.values('email_comprador').distinct().count()
    clientes_registrados = ventas_web.filter(comprador__isnull=False).values('comprador').distinct().count()
    porcentaje_clientes_registrados = (clientes_registrados / total_clientes * 100) if total_clientes else 0
    
    # Productos Más Vendidos (combinando ventas web y asignaciones)
    from django.db.models import Value, CharField
    from django.db.models.functions import Concat
    
    productos_vendidos_web = ventas_web_mes.filter(estado_pago='PAGADO').values(
        'producto__nombre'
    ).annotate(
        tipo=Value('Web', output_field=CharField()),
        unidades=Sum('cantidad'),
        ingresos=Sum('total'),
        costos=Sum(F('producto__costo') * F('cantidad')),
        ganancia=Sum('total') - Sum(F('producto__costo') * F('cantidad'))
    )
    
    productos_vendidos_asignacion = asignaciones_mes.values(
        'producto__nombre'
    ).annotate(
        tipo=Value('Asignación', output_field=CharField()),
        unidades=Sum('cantidad'),
        ingresos=Sum(
            Case(
                When(distribuidor__rol='DISTRIBUIDOR', then=F('producto__precio_distribuidor') * F('cantidad')),
                When(distribuidor__rol='REVENDEDOR', then=F('producto__precio_revendedor') * F('cantidad')),
                default=F('producto__precio') * F('cantidad'),
            )
        ),
        costos=Sum(F('producto__costo') * F('cantidad')),
        ganancia=F('ingresos') - F('costos')
    )
    
    productos_top = list(productos_vendidos_web) + list(productos_vendidos_asignacion)
    productos_top.sort(key=lambda x: x['unidades'], reverse=True)
    productos_top = productos_top[:5]

    # Set panel title based on user role
    panel_title = "Mi Panel" if request.user.rol == 'ADMIN' else "Panel de Administración"
    
    context = {
        'form': form,
        'asignaciones': asignaciones,
        'panel_title': panel_title,
        # Datos de ventas web
        'ventas': ventas_web.order_by('-fecha_venta'),
        'total_ventas_web': total_ventas_web,
        'costos_web': costos_web,
        'ganancias_web': ganancias_web,
        'porcentaje_costos_web': porcentaje_costos_web,
        'margen_ganancia_web': margen_ganancia_web,
        # Datos de asignaciones
        'total_ventas_asignacion': total_ventas_asignacion,
        'costos_asignacion': costos_asignacion,
        'ganancias_asignacion': ganancias_asignacion,
        'porcentaje_costos_asignacion': porcentaje_costos_asignacion,
        'margen_ganancia_asignacion': margen_ganancia_asignacion,
        'porcentaje_cambio_asignaciones': porcentaje_cambio_asignaciones,
        'total_distribuidores': total_distribuidores,
        'distribuidores_activos': distribuidores_activos,
        'porcentaje_distribuidores_activos': porcentaje_distribuidores_activos,
        # Totales combinados
        'total_ventas': total_ventas,
        'porcentaje_cambio_ventas': porcentaje_cambio_ventas,
        'costos_totales': costos_totales,
        'ganancias_netas': ganancias_netas,
        'porcentaje_costos': porcentaje_costos,
        'margen_ganancia': margen_ganancia,
        'porcentaje_ventas_web': porcentaje_ventas_web,
        'porcentaje_ventas_asignacion': porcentaje_ventas_asignacion,
        # Datos de clientes
        'total_clientes': total_clientes,
        'porcentaje_clientes_registrados': porcentaje_clientes_registrados,
        'productos_top': productos_top,
    }

    return render(request, 'core/asignar.html', context)

@login_required
def distribuidor_view(request):
    if request.user.rol != 'DISTRIBUIDOR':
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")

@login_required
def inventario_view(request):
    # Solo accesible para ADMIN o SUPERUSUARIO
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")

    productos = Producto.objects.all().order_by('nombre')
    form = StockForm()

    if request.method == 'POST':
        form = StockForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data['producto']
            cantidad = form.cleaned_data['cantidad']

            # Actualizar el stock del producto
            producto.stock = producto.stock + cantidad
            producto.save()

            messages.success(request, f'Se agregó {cantidad} unidades al producto "{producto.nombre}".')
            return redirect('core:inventario')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')

    context = {
        'productos': productos,
        'form': form,
    }
    return render(request, 'core/inventario.html', context)

@login_required
def asignar_distribuidor_view(request):
    if request.user.rol != 'DISTRIBUIDOR':
        return HttpResponseForbidden("No tiene permiso para acceder a esta sección.")
    
    if request.method == 'POST':
        form = AsignacionForm(request.POST, user=request.user)
        if form.is_valid():
            asignacion = form.save(commit=False)
            asignacion.admin = request.user
            
            # Verificar que solo pueda asignar a revendedores
            if form.cleaned_data['distribuidor'].rol != 'REVENDEDOR':
                messages.error(request, 'Como distribuidor, solo puede asignar stock a revendedores.')
                return redirect('core:asignar_distribuidor')
            
            asignacion.save()
            messages.success(request, 'Asignación creada correctamente.')
            return redirect('core:distribuidor')
        else:
            messages.error(request, 'Por favor corrija los errores en el formulario.')
    else:
        form = AsignacionForm(user=request.user)
    
    return render(request, 'core/asignar_distribuidor.html', {'form': form})

def carrito_view(request, producto_id=None):
    if producto_id:
        producto = get_object_or_404(Producto, id=producto_id)
        # Agregar producto al carrito
        if request.method == 'POST':
            cantidad = int(request.POST.get('cantidad', 1))
            if not request.session.session_key:
                request.session.create()
            
            # Verificar si hay productos en el carrito y si son del mismo tipo (exclusivo/no exclusivo)
            current_items = CarritoItem.objects.filter(session_key=request.session.session_key)
            if current_items.exists():
                current_cart_exclusivo = current_items.first().producto.es_exclusivo
                if current_cart_exclusivo != producto.es_exclusivo:
                    messages.error(request, "No se pueden mezclar productos de tiendas diferentes en el mismo carrito. Por favor, finalice la compra actual o limpie el carrito.")
                    return redirect('core:carrito')
            
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
                email_comprador=email,
                estado_pago='PENDIENTE'  # Set default state
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
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
        
    asignacion = get_object_or_404(Asignacion, id=asignacion_id)
    
    # Verificar permisos
    if request.user.rol in ['ADMIN', 'SUPERUSUARIO']:
        # Admins pueden cambiar cualquier asignación
        puede_cambiar = True
    elif request.user.rol == 'DISTRIBUIDOR':
        # Distribuidores solo pueden cambiar asignaciones que ellos hicieron a revendedores
        puede_cambiar = (asignacion.admin == request.user and asignacion.distribuidor.rol == 'REVENDEDOR')
    else:
        puede_cambiar = False
    
    if not puede_cambiar:
        return JsonResponse({'error': 'No tiene permiso para cambiar el estado.'}, status=403)
    
    try:
        nuevo_estado = 'PAGADO' if asignacion.estado == 'PENDIENTE' else 'PENDIENTE'
        asignacion.estado = nuevo_estado
        asignacion.save()
        
        messages.success(request, f'Estado de asignacion actualizado a {nuevo_estado}')
        return redirect('core:asignar')
    except Exception as e:
        messages.error(request, f'Error al cambiar el estado: {str(e)}')
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
    # if not request.user.is_authenticated:
    #     return redirect('core:login')
        
    if not request.user.is_authenticated or request.user.rol not in ['ADMIN', 'SUPERUSUARIO', 'DISTRIBUIDOR']:
        return HttpResponseForbidden("No tiene permiso para registrar usuarios.")
        
    if request.method == 'POST':
        form = UserCreationFormWithRol(request.POST, user=request.user)
        if form.is_valid():
            user = form.save(commit=False)
            # Si el rol es DISTRIBUIDOR, establecer es_distribuidor_exclusivo
            if user.rol == 'DISTRIBUIDOR':
                user.es_distribuidor_exclusivo = form.cleaned_data.get('es_distribuidor_exclusivo', False)
            user.save()
            # Crear cupón de descuento si es revendedor
            if user.rol == 'REVENDEDOR':
                from .models import CuponDescuento
                CuponDescuento.objects.create(
                    codigo=user.username,
                    revendedor=user,
                    descuento_porcentaje=10.00
                )
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
        ciudad = request.POST.get('ciudad')
        
        try:
            # Crear usuario con rol CLIENTE por defecto
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                email=email,
                nombre=nombre,
                dni=dni,
                ciudad=ciudad,
                domicilio=request.POST.get('domicilio', ''),
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
    
    # Verificar si hay productos exclusivos en el carrito
    tiene_productos_exclusivos = any(item.producto.es_exclusivo for item in items)
    
    if tiene_productos_exclusivos:
        # Buscar distribuidores exclusivos en la misma ciudad que el usuario
        ciudad_usuario = request.user.ciudad if request.user.is_authenticated else None
        if ciudad_usuario:
            distribuidor = CustomUser.objects.filter(
                rol='DISTRIBUIDOR',
                es_distribuidor_exclusivo=True,
                ciudad=ciudad_usuario
            ).first()
        else:
            distribuidor = None
        
        return render(request, 'core/checkout_exclusivo.html', {
            'items': items,
            'total': total,
            'distribuidor': distribuidor
        })
    else:
        # Checkout normal para productos convencionales
        return render(request, 'core/checkout.html', {
            'items': items,
            'total': total
        })

def checkout_exclusivo_view(request):
    """Vista para mostrar los datos del distribuidor exclusivo"""
    if not request.session.session_key:
        return redirect('core:carrito')
    
    # Obtener el ID de la última venta creada para este email
    email = request.session.get('email_comprador')
    if not email:
        return redirect('core:carrito')
    
    # Buscar las últimas ventas del usuario
    ventas = Venta.objects.filter(
        email_comprador=email,
        session_key=request.session.session_key
    ).order_by('-fecha_venta')
    
    if not ventas:
        messages.error(request, 'No se encontraron ventas asociadas.')
        return redirect('core:carrito')
    
    # Calcular el total de las ventas
    total = sum(venta.total for venta in ventas)
    
    # Buscar un distribuidor exclusivo en la misma ciudad
    ciudad_usuario = request.user.ciudad if request.user.is_authenticated else None
    if ciudad_usuario:
        distribuidor = CustomUser.objects.filter(
            rol='DISTRIBUIDOR',
            es_distribuidor_exclusivo=True,
            ciudad=ciudad_usuario
        ).first()
    else:
        distribuidor = None
    
    return render(request, 'core/checkout_exclusivo.html', {
        'ventas': ventas,
        'total': total,
        'distribuidor': distribuidor
    })

def pago_transferencia_view(request):
    """Vista para mostrar los datos de transferencia bancaria"""
    if not request.session.session_key:
        return redirect('core:carrito')
    
    # Obtener el ID de la última venta creada para este email
    email = request.session.get('email_comprador')
    if not email:
        return redirect('core:carrito')
    
    # Obtener las ventas recientes del usuario
    ventas = Venta.objects.filter(
        email_comprador=email,
        session_key=request.session.session_key
    ).order_by('-fecha_venta')
    
    if not ventas:
        messages.error(request, 'No se encontraron ventas asociadas.')
        return redirect('core:carrito')
    
    # Obtener los items de las ventas
    items = []
    for venta in ventas:
        items.append({
            'producto': venta.producto,
            'cantidad': venta.cantidad
        })
    
    # Calcular el total
    total = sum(venta.total for venta in ventas)
    venta_id = ventas.first().id if ventas else None
    
    return render(request, 'core/pago_transferencia.html', {
        'items': items,
        'total': total,
        'venta_id': venta_id
    })

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
        ciudad = request.POST.get('ciudad', '').strip()
        codigo_cupon = request.POST.get('codigo_cupon', '').strip()
        
        # Validar campos obligatorios
        if not all([nombre, email, dni, ciudad]):
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
            user.ciudad = ciudad
            user.save()
            comprador = user
        
        total_venta = Decimal('0')
        ventas = []

        # Verificar si hay productos exclusivos
        tiene_productos_exclusivos = any(item.producto.es_exclusivo for item in items)

        # Validar y aplicar cupón de descuento
        descuento_porcentaje = Decimal('0')
        if codigo_cupon:
            from .models import CuponDescuento
            try:
                cupon = CuponDescuento.objects.get(codigo=codigo_cupon)
                descuento_porcentaje = cupon.descuento_porcentaje
                messages.success(request, f'Cupón aplicado: {descuento_porcentaje}% de descuento.')
            except CuponDescuento.DoesNotExist:
                messages.error(request, 'Código de cupón inválido.')
                return redirect('core:checkout')

        # Crear las ventas
        for item in items:
            subtotal = item.producto.precio * item.cantidad
            total_venta += subtotal
            
            # Aplicar descuento si hay cupón válido
            if descuento_porcentaje > 0:
                subtotal = subtotal * (Decimal('100') - descuento_porcentaje) / Decimal('100')
            
            venta = Venta.objects.create(
                producto=item.producto,
                cantidad=item.cantidad,
                total=subtotal,
                email_comprador=email,
                nombre_comprador=nombre,
                comprador=comprador,
                estado_pago='PENDIENTE',
                session_key=request.session.session_key
            )
            ventas.append(venta.id)
        
        # Limpiar el carrito después de crear las ventas
        items.delete()
        
        # Guardar el ID de la última venta para mostrarlo
        request.session['ultima_venta_id'] = ventas[-1]
        request.session['email_comprador'] = email
        
        messages.success(request, f'¡Compra exitosa! Tu número de pedido es #{ventas[-1]}')
        
        # Redirigir según el tipo de productos
        if tiene_productos_exclusivos:
            return redirect('core:checkout_exclusivo')
        else:
            return redirect('core:pago_transferencia')
            
    except Exception as e:
        messages.error(request, f'Error al procesar la compra: {str(e)}')
        return redirect('core:checkout')

@login_required
def cambiar_estado_venta(request, venta_id):
    """Vista para cambiar el estado de una venta web"""
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tiene permiso para cambiar el estado.")
    
    venta = get_object_or_404(Venta, id=venta_id)
    producto = venta.producto
    
    if venta.estado_pago == 'PENDIENTE':
        # Cambiar a PAGADO y descontar stock
        if producto.stock >= venta.cantidad:
            producto.stock -= venta.cantidad
            producto.save()
            venta.estado_pago = 'PAGADO'
            venta.save()
            messages.success(request, f'Venta marcada como PAGADO y stock actualizado.')
        else:
            messages.error(request, f'Stock insuficiente para completar la venta.')
    else:
        # Cambiar a PENDIENTE y revertir stock
        producto.stock += venta.cantidad
        producto.save()
        venta.estado_pago = 'PENDIENTE'
        venta.save()
        messages.success(request, f'Venta marcada como PENDIENTE y stock revertido.')
    
    return redirect('core:asignar')

from django.http import HttpResponseRedirect
from django.urls import reverse

@login_required
def perfil_view(request):
    """Vista para mostrar el perfil del usuario"""
    # Obtener estadísticas del usuario
    total_compras = Venta.objects.filter(comprador=request.user).count()
    total_gastado = Venta.objects.filter(comprador=request.user).aggregate(total=Sum('total'))['total'] or 0
    fecha_registro = request.user.date_joined

    context = {
        'total_compras': total_compras,
        'total_gastado': total_gastado,
        'fecha_registro': fecha_registro,
    }
    return render(request, 'core/perfil.html', context)

@login_required
def editar_perfil_view(request):
    """Vista para editar el perfil del usuario"""
    if request.method == 'POST':
        # Obtener los datos del formulario
        user = request.user
        user.nombre = request.POST.get('nombre')
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.dni = request.POST.get('dni')
        user.domicilio = request.POST.get('domicilio')
        user.telefono = request.POST.get('telefono')
        
        try:
            user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('core:perfil')
        except Exception as e:
            messages.error(request, f'Error al actualizar el perfil: {str(e)}')
            return redirect('core:editar_perfil')
    
    return render(request, 'core/editar_perfil.html')

def contact_view(request):
    """Vista para procesar el formulario de contacto"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')
        
        if not all([name, email, message]):
            messages.error(request, 'Por favor complete todos los campos.')
            return HttpResponseRedirect(reverse('core:home') + '#contact')
        
        # Aquí se podría agregar el código para enviar el email
        messages.success(request, 'Mensaje enviado correctamente. Nos pondremos en contacto pronto.')
        return HttpResponseRedirect(reverse('core:home') + '#contact')
    
    # Si es GET, redirigir a la página de inicio con el ancla del formulario de contacto
    return HttpResponseRedirect(reverse('core:home') + '#contact')
