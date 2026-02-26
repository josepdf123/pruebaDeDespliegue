from decimal import Decimal
from django.db import models


class Rol(models.Model):
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

    class Meta:
        verbose_name = "Rol"
        verbose_name_plural = "Roles"


class Usuario(models.Model):
    idRol = models.ForeignKey(Rol, on_delete=models.PROTECT, related_name='usuarios', verbose_name="Rol")
    usuario = models.CharField(max_length=50, unique=True)
    contrasena = models.CharField(max_length=255, verbose_name="Contraseña")
    correo = models.EmailField(unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    token_recuperacion = models.CharField(max_length=255, blank=True, null=True)
    # Campos para bloqueo de cuenta (aporte Yonatan)
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.usuario})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"


class Estado(models.Model):
    descripcion = models.CharField(max_length=50)

    def __str__(self):
        return self.descripcion

    class Meta:
        verbose_name = "Estado"
        verbose_name_plural = "Estados"


class Mesa(models.Model):
    idUsuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='mesas', verbose_name="Usuario")
    estado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='mesas')
    numMesa = models.IntegerField(unique=True, verbose_name="Número de Mesa")
    capacidad = models.IntegerField()

    def __str__(self):
        return f"Mesa {self.numMesa}"

    class Meta:
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"
        ordering = ['numMesa']


class Plato(models.Model):
    idUsuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='platos', verbose_name="Usuario")
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Plato"
        verbose_name_plural = "Platos"


class Menu(models.Model):
    TIPO_CHOICES = [
        ('desayuno', 'Desayuno'),
        ('almuerzo', 'Almuerzo'),
        ('cena', 'Cena'),
        ('especial', 'Especial'),
    ]
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Menú"
        verbose_name_plural = "Menús"


class MenuPlato(models.Model):
    idMenu = models.ForeignKey(Menu, on_delete=models.CASCADE, related_name='menu_platos')
    idPlato = models.ForeignKey(Plato, on_delete=models.CASCADE, related_name='menu_platos')
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.nombre} - {self.idMenu}"

    class Meta:
        verbose_name = "Menú Plato"
        verbose_name_plural = "Menú Platos"


class Pedido(models.Model):
    idUsuario = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='pedidos', verbose_name="Usuario")
    idMesa = models.ForeignKey(Mesa, on_delete=models.PROTECT, related_name='pedidos', verbose_name="Mesa")
    idEstado = models.ForeignKey(Estado, on_delete=models.PROTECT, related_name='pedidos', verbose_name="Estado")
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def calcular_total(self):
        total = sum(d.subtotal() for d in self.detalles.all())
        self.total = total
        self.save()

    def __str__(self):
        return f"Pedido #{self.pk} - Mesa {self.idMesa.numMesa}"

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-fecha']


class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    plato = models.ForeignKey(Plato, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    notas = models.CharField(max_length=200, blank=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.cantidad}x {self.plato.nombre}"

    class Meta:
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedido"


class CierreCaja(models.Model):
    # Aporte de Yonatan
    fecha = models.DateField(auto_now_add=True)
    efectivo = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    electronico = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_ventas = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    registrado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='cierres')

    def total(self):
        return Decimal(str(self.efectivo)) + Decimal(str(self.electronico))

    def __str__(self):
        return f"Cierre {self.fecha} - Total: ${self.total()}"

    class Meta:
        verbose_name = "Cierre de Caja"
        verbose_name_plural = "Cierres de Caja"
        ordering = ['-fecha']
