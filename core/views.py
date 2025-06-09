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
from .forms import CustomLoginForm, AsignacionForm, UserCreationFormWithRol, ProductoForm
from decimal import Decimal
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta

# ... [rest of the file content remains the same] ...
