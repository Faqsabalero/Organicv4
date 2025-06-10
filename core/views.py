from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import logout, login
from .models import CustomUser, Producto, Asignacion, CarritoItem, Venta
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
def ventas_web_view(request):
    """
    Vista para mostrar el panel de ventas web.
    Solo accesible para usuarios autenticados con rol de ADMIN o SUPERUSUARIO.
    """
    if request.user.rol not in ['ADMIN', 'SUPERUSUARIO']:
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    
    try:
        # Obtener todas las ventas ordenadas por fecha descendente
        ventas = Venta.objects.all().order_by('-id')
        
        # Paginación
        paginator = Paginator(ventas, 10)  # 10 ventas por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Si se solicita descargar CSV
        if request.GET.get('download_csv'):
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="ventas.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['ID', 'Cliente', 'Total', 'Estado', 'Fecha'])
            
            for venta in ventas:
                writer.writerow([
                    venta.id,
                    venta.comprador.username if venta.comprador else 'N/A',
                    venta.total,
                    venta.estado,
                    venta.fecha.strftime('%Y-%m-%d %H:%M:%S')
                ])
            
            return response
        
        context = {
            'page_obj': page_obj,
            'total_ventas': ventas.count(),
        }
        
        return render(request, 'core/ventas_web.html', context)
        
    except Exception as e:
        messages.error(request, f"Error al cargar las ventas: {str(e)}")
        return render(request, 'core/ventas_web.html', {'page_obj': None, 'total_ventas': 0})

# ... [rest of the file content remains the same] ...
