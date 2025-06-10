from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('gestionar-productos/', views.gestionar_productos_view, name='gestionar_productos'),
    path('crear-producto/', views.crear_producto_view, name='crear_producto'),
    path('editar-producto/<int:producto_id>/', views.editar_producto_view, name='editar_producto'),
    path('', views.home_view, name='home'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('asignar/', views.asignar_view, name='asignar'),
    path('distribuidor/', views.distribuidor_view, name='distribuidor'),
    path('distribuidor/asignar/', views.asignar_distribuidor_view, name='asignar_distribuidor'),
    path('revendedor/', views.revendedor_view, name='revendedor'),
    path('carrito/', views.carrito_view, name='carrito'),
    path('carrito/<int:producto_id>/', views.carrito_view, name='agregar_carrito'),
    path('carrito/eliminar/<int:item_id>/', views.eliminar_carrito_item, name='eliminar_carrito_item'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout-exclusivo/', views.checkout_exclusivo_view, name='checkout_exclusivo'),
    path('procesar-pago/', views.procesar_pago, name='procesar_pago'),
    path('pago-transferencia/', views.pago_transferencia_view, name='pago_transferencia'),
    path('registro-rapido/', views.registro_rapido, name='registro_rapido'),
    path('procesar-compra-carrito/', views.procesar_compra_carrito, name='procesar_compra_carrito'),
    path('register/', views.register_user, name='register'),
    path('cambiar-estado/<int:asignacion_id>/', views.cambiar_estado_asignacion, name='cambiar_estado_asignacion'),
    path('tienda-oculta/', views.tienda_oculta_view, name='tienda_oculta'),
    path('contact/', views.contact_view, name='contact'),
]
