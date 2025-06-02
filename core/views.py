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

[... mantener el resto del código sin cambios hasta asignar_view ...]

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
    
    # Obtener las asignaciones para la pestaña "Asignaciones"
    asignaciones = Asignacion.objects.all().order_by('-fecha_asignacion')

    # Obtener las ventas web para la pestaña "Ventas"
    from django.db.models import Sum, Count, F
    from django.utils import timezone
    from datetime import timedelta
    
    hoy = timezone.now()
    mes_actual = hoy.month
    mes_anterior = (hoy - timedelta(days=30)).month
    
    # Filtrar solo ventas web (todas las ventas son web)
    ventas_web = Venta.objects.all()
    ventas_web_mes = ventas_web.filter(fecha_venta__month=mes_actual)
    ventas_web_mes_anterior = ventas_web.filter(fecha_venta__month=mes_anterior)
    
    total_ventas_web = ventas_web_mes.aggregate(total=Sum('total', default=0))['total'] or 0
    total_ventas_anterior = ventas_web_mes_anterior.aggregate(total=Sum('total', default=0))['total'] or 1
    
    porcentaje_cambio_ventas = ((total_ventas_web - total_ventas_anterior) / total_ventas_anterior) * 100
    
    costos_totales_web = ventas_web_mes.aggregate(
        costos=Sum(F('producto__costo') * F('cantidad'), default=0)
    )['costos'] or 0
    
    ganancias_netas_web = total_ventas_web - costos_totales_web
    porcentaje_costos = (costos_totales_web / total_ventas_web * 100) if total_ventas_web else 0
    margen_ganancia = (ganancias_netas_web / total_ventas_web * 100) if total_ventas_web else 0
    
    total_clientes = ventas_web.values('email_comprador').distinct().count()
    clientes_registrados = ventas_web.filter(comprador__isnull=False).values('comprador').distinct().count()
    porcentaje_clientes_registrados = (clientes_registrados / total_clientes * 100) if total_clientes else 0

    # Set panel title based on user role
    panel_title = "Mi Panel" if request.user.rol == 'ADMIN' else "Panel de Administración"
    
    context = {
        'form': form,
        'asignaciones': asignaciones,
        'panel_title': panel_title,
        # Datos de ventas web
        'ventas': ventas_web.order_by('-fecha_venta'),
        'total_ventas': total_ventas_web,
        'porcentaje_cambio_ventas': porcentaje_cambio_ventas,
        'costos_totales': costos_totales_web,
        'ganancias_netas': ganancias_netas_web,
        'porcentaje_costos': porcentaje_costos,
        'margen_ganancia': margen_ganancia,
        'total_clientes': total_clientes,
        'porcentaje_clientes_registrados': porcentaje_clientes_registrados,
    }

    return render(request, 'core/asignar.html', context)

[... mantener el resto del código sin cambios ...]
