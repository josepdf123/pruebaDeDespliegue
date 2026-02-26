# core/admin.py

from django.contrib import admin
from .models import Rol, Usuario, Estado, Mesa, Plato, Menu, MenuPlato, Pedido
from .models import DetallePedido 

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ['id', 'descripcion']


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['id', 'usuario', 'nombre', 'apellido', 'correo', 'idRol']


@admin.register(Estado)
class EstadoAdmin(admin.ModelAdmin):
    list_display = ['id', 'descripcion']


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ['id', 'numMesa', 'capacidad', 'estado', 'idUsuario']


@admin.register(Plato)
class PlatoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'precio', 'idUsuario']


@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'tipo']


@admin.register(MenuPlato)
class MenuPlatoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'precio', 'idMenu', 'idPlato']


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'idMesa', 'idUsuario', 'idEstado', 'fecha']

@admin.register(DetallePedido)
class DetallePedidoAdmin(admin.ModelAdmin):
    list_display = ['pedido', 'plato', 'cantidad', 'precio_unitario']