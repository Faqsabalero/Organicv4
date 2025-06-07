from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROL_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DISTRIBUIDOR', 'Distribuidor'),
        ('REVENDEDOR', 'Revendedor'),
        ('SUPERUSUARIO', 'Superusuario'),
        ('CLIENTE', 'Cliente'),
    )
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='CLIENTE')
    nombre = models.CharField(max_length=100, blank=True, null=True)
    dni = models.CharField(max_length=20, blank=True, null=True)
    ciudad = models.TextField(blank=True, null=True)
    es_distribuidor_exclusivo = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        # Si el usuario es un superusuario, asignar el rol SUPERUSUARIO
        if self.is_superuser:
            self.rol = 'SUPERUSUARIO'
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    precio_distribuidor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_revendedor = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    costo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    imagen_url = models.URLField()
    es_exclusivo = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

class CarritoItem(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40)

    class Meta:
        ordering = ['-fecha_agregado']

class Asignacion(models.Model):
    PLAN_PAGO_CHOICES = (
        ('1', 'Cuota 1'),
        ('2', 'Cuota 2'),
        ('3', 'Cuota 3'),
        ('4', 'Cuota 4'),
    )
    
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
    )
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='asignaciones_admin')
    distribuidor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='asignaciones_distribuidor')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    plan_pago = models.CharField(max_length=20, choices=PLAN_PAGO_CHOICES)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')

    def __str__(self):
        return f'{self.producto.nombre} - {self.distribuidor.username}'

class Venta(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('CANCELADO', 'Cancelado'),
    )
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_venta = models.DateTimeField(auto_now_add=True)
    email_comprador = models.EmailField(null=True, blank=True)
    nombre_comprador = models.CharField(max_length=100, null=True, blank=True)
    comprador = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    estado_pago = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    
    def __str__(self):
        return f'Venta {self.id} - {self.producto.nombre}'
    
    class Meta:
        ordering = ['-fecha_venta']
