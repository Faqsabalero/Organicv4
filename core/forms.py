from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from .models import CustomUser, Asignacion, Producto

class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(
            attrs={
                'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600',
                'placeholder': 'Usuario'
            }
        )
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600',
                'placeholder': 'Contraseña'
            }
        )
    )

class UserCreationFormWithRol(UserCreationForm):
    CIUDADES_CHOICES = [
        ('', 'Seleccione una ciudad'),
        ('santa fe', 'Santa Fe'),
        ('cordoba', 'Córdoba'),
        ('rosario', 'Rosario'),
        ('esperanza', 'Esperanza'),
        ('rafaela', 'Rafaela'),
    ]

    ciudad = forms.ChoiceField(
        choices=CIUDADES_CHOICES,
        widget=forms.Select(
            attrs={
                'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600',
            }
        ),
    )

    es_distribuidor_exclusivo = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(
            attrs={
                'class': 'h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded',
            }
        )
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'rol', 'password1', 'password2', 'nombre', 'dni', 'ciudad', 'es_distribuidor_exclusivo')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar clases de Tailwind CSS a los campos
        for field in self.fields:
            if field != 'ciudad':  # Skip ciudad as it's already configured
                self.fields[field].widget.attrs.update({
                    'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600'
                })
        # Filtrar las opciones del campo rol según el usuario
        if 'rol' in self.fields:
            if user:
                if user.rol == 'ADMIN':
                    # Si es ADMIN, solo mostrar DISTRIBUIDOR y REVENDEDOR
                    choices = [choice for choice in self.fields['rol'].choices if choice[0] in ['DISTRIBUIDOR', 'REVENDEDOR']]
                elif user.rol == 'DISTRIBUIDOR':
                    # Si es DISTRIBUIDOR, solo mostrar REVENDEDOR
                    choices = [choice for choice in self.fields['rol'].choices if choice[0] == 'REVENDEDOR']
                else:
                    # Para SUPERUSUARIO, mostrar todos excepto SUPERUSUARIO
                    choices = [choice for choice in self.fields['rol'].choices if choice[0] != 'SUPERUSUARIO']
            self.fields['rol'].choices = choices

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'precio', 'costo', 'imagen_url', 'es_exclusivo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600'}),
            'descripcion': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600', 'rows': 4}),
            'precio': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600', 'min': '0', 'step': '0.01'}),
            'costo': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600', 'min': '0', 'step': '0.01'}),
            'imagen_url': forms.URLInput(attrs={'class': 'w-full px-4 py-2 border border-green-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-600'}),
            'es_exclusivo': forms.CheckboxInput(attrs={'class': 'h-4 w-4 rounded border-gray-300 text-green-600 focus:ring-green-500'}),
        }

class AsignacionForm(forms.ModelForm):
    class Meta:
        model = Asignacion
        fields = ['distribuidor', 'producto', 'cantidad', 'plan_pago']
        widgets = {
            'distribuidor': forms.Select(
                attrs={
                    'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm transition duration-150 ease-in-out'
                }
            ),
            'producto': forms.Select(
                attrs={
                    'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm transition duration-150 ease-in-out'
                }
            ),
            'cantidad': forms.NumberInput(
                attrs={
                    'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm transition duration-150 ease-in-out',
                    'min': '1'
                }
            ),
            'plan_pago': forms.Select(
                attrs={
                    'class': 'mt-1 block w-full rounded-lg border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500 sm:text-sm transition duration-150 ease-in-out'
                }
            )
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar distribuidores según el rol del usuario
        if user:
            if user.rol == 'DISTRIBUIDOR':
                # Si es distribuidor, solo mostrar revendedores
                self.fields['distribuidor'].queryset = CustomUser.objects.filter(rol='REVENDEDOR')
            elif user.rol in ['ADMIN', 'SUPERUSUARIO']:
                # Si es admin o superusuario, mostrar distribuidores y revendedores
                self.fields['distribuidor'].queryset = CustomUser.objects.filter(
                    rol__in=['DISTRIBUIDOR', 'REVENDEDOR']
                )
