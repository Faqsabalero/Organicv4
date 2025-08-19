from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Producto, Asignacion, CustomUser

class StockForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.all(),
        label="Producto",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    cantidad = forms.IntegerField(
        min_value=1,
        label="Cantidad a agregar",
        widget=forms.NumberInput(attrs={'class': 'form-input'})
    )

class AsignacionForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    class Meta:
        model = Asignacion
        fields = ['distribuidor', 'producto', 'cantidad', 'plan_pago', 'estado']
        widgets = {
            'distribuidor': forms.Select(attrs={'class': 'form-select'}),
            'producto': forms.Select(attrs={'class': 'form-select'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'plan_pago': forms.Select(attrs={'class': 'form-select'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

class UserCreationFormWithRol(UserCreationForm):
    ROL_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DISTRIBUIDOR', 'Distribuidor'),
        ('REVENDEDOR', 'Revendedor'),
        ('SUPERUSUARIO', 'Superusuario'),
        ('CLIENTE', 'Cliente'),
    )
    rol = forms.ChoiceField(choices=ROL_CHOICES, label="Rol de usuario")

    nombre = forms.CharField(max_length=100, required=False, label="Nombre Completo")
    dni = forms.CharField(max_length=20, required=False, label="DNI")
    ciudad = forms.CharField(max_length=100, required=False, label="Ciudad")
    provincia = forms.CharField(max_length=100, required=False, label="Provincia")
    domicilio = forms.CharField(max_length=200, required=False, label="Domicilio")
    telefono = forms.CharField(max_length=20, required=False, label="Teléfono")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'rol', 'nombre', 'dni', 'ciudad', 'provincia', 'domicilio', 'telefono', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar opciones de rol según el usuario actual
        if self.user and self.user.rol == 'ADMIN':
            # Los administradores no pueden crear superusuarios ni otros administradores
            self.fields['rol'].choices = [
                ('DISTRIBUIDOR', 'Distribuidor'),
                ('REVENDEDOR', 'Revendedor'),
                ('CLIENTE', 'Cliente'),
            ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = self.cleaned_data['rol']
        user.nombre = self.cleaned_data.get('nombre', '')
        user.dni = self.cleaned_data.get('dni', '')
        user.ciudad = self.cleaned_data.get('ciudad', '')
        user.provincia = self.cleaned_data.get('provincia', '')
        user.domicilio = self.cleaned_data.get('domicilio', '')
        user.telefono = self.cleaned_data.get('telefono', '')
        if commit:
            user.save()
        return user

class RegistroRapidoForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'pl-10 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
            'placeholder': '••••••••'
        }),
        label="Contraseña",
        min_length=6,
        help_text="Mínimo 6 caracteres"
    )
    
    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'nombre', 'email', 'dni', 'ciudad', 'domicilio')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'pl-10 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'usuario123'
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'pl-10 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Tu nombre completo'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'pl-10 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'tu@email.com'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'pl-10 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': '12345678',
                'pattern': '[0-9]{7,8}'
            }),
            'ciudad': forms.Select(attrs={
                'class': 'pl-10 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200'
            }, choices=[
                ('', 'Seleccione una ciudad'),
                ('santa fe', 'Santa Fe'),
                ('cordoba', 'Córdoba'),
                ('rosario', 'Rosario'),
                ('esperanza', 'Esperanza'),
                ('rafaela', 'Rafaela'),
            ]),
            'domicilio': forms.TextInput(attrs={
                'class': 'pl-10 block w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent transition-all duration-200',
                'placeholder': 'Calle 123, Ciudad'
            }),
        }
        labels = {
            'username': 'Nombre de Usuario',
            'nombre': 'Nombre Completo',
            'email': 'Email',
            'dni': 'DNI',
            'ciudad': 'Ciudad',
            'domicilio': 'Domicilio (opcional)',
        }
    
    def clean_dni(self):
        dni = self.cleaned_data.get('dni')
        if dni:
            # Remover caracteres no numéricos
            dni = ''.join(filter(str.isdigit, dni))
            if len(dni) < 7 or len(dni) > 8:
                raise forms.ValidationError('El DNI debe tener entre 7 y 8 dígitos.')
        return dni
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email ya está registrado.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.rol = 'CLIENTE'
        if commit:
            user.save()
        return user
