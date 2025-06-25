from django import forms
from .models import Producto

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
