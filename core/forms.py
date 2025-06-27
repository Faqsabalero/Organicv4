from django import forms
from .models import Producto, Asignacion

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

class UserCreationFormWithRol(forms.UserCreationForm):
    ROL_CHOICES = (
        ('ADMIN', 'Admin'),
        ('DISTRIBUIDOR', 'Distribuidor'),
        ('REVENDEDOR', 'Revendedor'),
        ('SUPERUSUARIO', 'Superusuario'),
        ('CLIENTE', 'Cliente'),
    )
    rol = forms.ChoiceField(choices=ROL_CHOICES, label="Rol de usuario")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'rol', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.rol = self.cleaned_data['rol']
        if commit:
            user.save()
        return user
