# core/forms.py

from django import forms
from .models import Mesa, Plato, Menu, MenuPlato, Estado, Usuario, Pedido, Rol


class MesaForm(forms.ModelForm):
    class Meta:
        model = Mesa
        fields = ['numMesa', 'capacidad', 'estado']
        labels = {
            'numMesa': 'Número de Mesa',
            'capacidad': 'Capacidad',
            'estado': 'Estado',
        }
        widgets = {
            'numMesa': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 1'}),
            'capacidad': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ej: 4'}),
            'estado': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['estado'].queryset = Estado.objects.filter(
            descripcion__in=['Disponible', 'Reservada', 'Ocupada']
        )

class PlatoForm(forms.ModelForm):
    class Meta:
        model = Plato
        fields = ['nombre', 'descripcion', 'precio']
        labels = {
            'nombre': 'Nombre del Plato',
            'descripcion': 'Descripción',
            'precio': 'Precio',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Bandeja Paisa'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

class MenuForm(forms.ModelForm):
    class Meta:
        model = Menu
        fields = ['nombre', 'tipo']
        labels = {
            'nombre': 'Nombre del Menú',
            'tipo': 'Tipo',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej: Menú del día'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }


class MenuPlatoForm(forms.ModelForm):
    class Meta:
        model = MenuPlato
        fields = ['idMenu', 'idPlato', 'nombre', 'descripcion', 'precio']
        labels = {
            'idMenu': 'Menú',
            'idPlato': 'Plato',
            'nombre': 'Nombre en Menú',
            'descripcion': 'Descripción',
            'precio': 'Precio',
        }
        widgets = {
            'idMenu': forms.Select(attrs={'class': 'form-select'}),
            'idPlato': forms.Select(attrs={'class': 'form-select'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }


class UsuarioForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['usuario', 'contrasena', 'correo', 'nombre', 'apellido', 'idRol']
        labels = {
            'usuario': 'Usuario',
            'contrasena': 'Contraseña',
            'correo': 'Correo',
            'nombre': 'Nombre',
            'apellido': 'Apellido',
            'idRol': 'Rol',
        }
        widgets = {
            'usuario': forms.TextInput(attrs={'class': 'form-control'}),
            'contrasena': forms.PasswordInput(attrs={'class': 'form-control', 'autocomplete': 'new-password'}),
            'correo': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'idRol': forms.Select(attrs={'class': 'form-select'}),
        }


class PedidoForm(forms.ModelForm):
    class Meta:
        model = Pedido
        fields = ['idUsuario', 'idMesa', 'idEstado']
        labels = {
            'idUsuario': 'Usuario',
            'idMesa': 'Mesa',
            'idEstado': 'Estado',
        }
        widgets = {
            'idUsuario': forms.Select(attrs={'class': 'form-select'}),
            'idMesa': forms.Select(attrs={'class': 'form-select'}),
            'idEstado': forms.Select(attrs={'class': 'form-select'}),
        }