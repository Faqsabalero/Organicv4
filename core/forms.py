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
    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'nombre', 'email', 'dni', 'ciudad', 'domicilio')
        widgets = {
            'password': forms.PasswordInput(),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        user.rol = 'CLIENTE'
        if commit:
            user.save()
        return user
