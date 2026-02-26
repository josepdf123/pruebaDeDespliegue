# core/views.py
from decimal import Decimal
import uuid
from datetime import date, timedelta
from django.core.mail import send_mail
from django.conf import settings as django_settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum
from django.db.models.deletion import ProtectedError
from django.utils import timezone
from django.utils.timezone import now
from .forms import MesaForm, PlatoForm, MenuForm, MenuPlatoForm, UsuarioForm, PedidoForm
from .models import Mesa, Plato, Menu, MenuPlato, Estado, Usuario, Pedido, Rol, DetallePedido, CierreCaja


# ─── DECORADORES DE SEGURIDAD ─────────────────────────────────────────────────

def login_requerido(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            messages.error(request, 'Debes iniciar sesión para acceder.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    wrapper.__name__ = view_func.__name__
    return wrapper


def rol_requerido(*roles_permitidos):
    def decorador(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.session.get('usuario_id'):
                messages.error(request, 'Debes iniciar sesión para acceder.')
                return redirect('login')
            rol_actual = request.session.get('usuario_rol', '')
            if rol_actual not in roles_permitidos:
                messages.error(request, 'No tienes permiso para acceder a esta sección.')
                return redirect('acceso_denegado')
            return view_func(request, *args, **kwargs)
        wrapper.__name__ = view_func.__name__
        return wrapper
    return decorador


# ─── AUTH ─────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.session.get('usuario_id'):
        return redirect('dashboard')

    if request.method == 'POST':
        usuario_input = request.POST.get('usuario')
        contrasena_input = request.POST.get('contrasena')
        try:
            usuario = Usuario.objects.get(usuario=usuario_input)

            # Verificar si está bloqueado (aporte Yonatan)
            if usuario.bloqueado_hasta and usuario.bloqueado_hasta > timezone.now():
                tiempo_restante = (usuario.bloqueado_hasta - timezone.now()).seconds
                minutos = tiempo_restante // 60
                segundos = tiempo_restante % 60
                messages.error(request, f'Usuario bloqueado. Intenta de nuevo en {minutos}m {segundos}s.')
                return render(request, 'core/login.html')

            # Verificar contraseña
            if usuario.contrasena == contrasena_input:
                usuario.intentos_fallidos = 0
                usuario.bloqueado_hasta = None
                usuario.save()
                request.session['usuario_id'] = usuario.pk
                request.session['usuario_nombre'] = usuario.nombre
                request.session['usuario_rol'] = usuario.idRol.descripcion
                messages.success(request, f'¡Bienvenido, {usuario.nombre}!')
                return redirect('dashboard')
            else:
                usuario.intentos_fallidos += 1
                if usuario.intentos_fallidos >= 3:
                    usuario.bloqueado_hasta = timezone.now() + timedelta(minutes=2)
                    usuario.intentos_fallidos = 0
                    usuario.save()
                    messages.error(request, 'Demasiados intentos fallidos. Usuario bloqueado por 2 minutos.')
                else:
                    intentos_restantes = 3 - usuario.intentos_fallidos
                    usuario.save()
                    messages.error(request, f'Contraseña incorrecta. Te quedan {intentos_restantes} intento(s).')

        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'core/login.html')


def dashboard(request):
    if not request.session.get('usuario_id'):
        return redirect('login')
    rol = request.session.get('usuario_rol', '')
    if rol == 'Administrador':
        return redirect('mesas_lista')
    elif rol == 'Mesero':
        return redirect('panel_mesero')
    elif rol == 'Cocinero':
        return redirect('panel_cocina')
    elif rol == 'Cajero':
        return redirect('panel_cajero')
    else:
        return redirect('login')


def logout_view(request):
    request.session.flush()
    messages.success(request, 'Sesión cerrada correctamente.')
    return redirect('login')


def recuperar_contrasena(request):
    if request.method == 'POST':
        correo = request.POST.get('correo')
        try:
            usuario = Usuario.objects.get(correo=correo)
            token = str(uuid.uuid4())
            usuario.token_recuperacion = token
            usuario.save()
            enlace = request.build_absolute_uri(f'/reset-password/{token}/')
            send_mail(
                subject='Recuperación de contraseña - Restaurante',
                message=f'Hola {usuario.nombre},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña:\n{enlace}\n\nSi no solicitaste esto, ignora este correo.',
                from_email=django_settings.DEFAULT_FROM_EMAIL,
                recipient_list=[correo],
            )
            messages.success(request, 'Te enviamos un correo con el enlace de recuperación.')
        except Usuario.DoesNotExist:
            messages.error(request, 'No existe una cuenta con ese correo.')
    return render(request, 'core/recuperar_contrasena.html')


def reset_password(request, token):
    try:
        usuario = Usuario.objects.get(token_recuperacion=token)
    except Usuario.DoesNotExist:
        messages.error(request, 'El enlace no es válido o ya fue usado.')
        return redirect('login')
    if request.method == 'POST':
        nueva = request.POST.get('contrasena')
        confirmar = request.POST.get('confirmar')
        if nueva == confirmar:
            usuario.contrasena = nueva
            usuario.token_recuperacion = None
            usuario.save()
            messages.success(request, '¡Contraseña actualizada! Ya puedes iniciar sesión.')
            return redirect('login')
        else:
            messages.error(request, 'Las contraseñas no coinciden.')
    return render(request, 'core/reset_password.html', {'token': token})


def acceso_denegado(request):
    return render(request, 'core/acceso_denegado.html')


# ─── MESAS ────────────────────────────────────────────────────────────────────

@rol_requerido('Administrador')
def mesas_lista(request):
    mesas = Mesa.objects.select_related('estado').all()
    form = MesaForm()
    if request.method == 'POST':
        form = MesaForm(request.POST)
        if form.is_valid():
            mesa = form.save(commit=False)
            mesa.idUsuario = Usuario.objects.get(pk=request.session['usuario_id'])
            mesa.save()
            messages.success(request, '¡Mesa agregada correctamente!')
            return redirect('mesas_lista')
        else:
            messages.error(request, 'Error al agregar la mesa. Revisa los datos.')
    return render(request, 'core/mesas.html', {'mesas': mesas, 'form': form})


@rol_requerido('Administrador')
def mesa_eliminar(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        try:
            mesa.delete()
            messages.success(request, f'Mesa {mesa.numMesa} eliminada.')
        except Exception:
            messages.error(request, f'No se puede eliminar la Mesa {mesa.numMesa} porque tiene registros asociados.')
    return redirect('mesas_lista')


@rol_requerido('Administrador')
def mesa_editar(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    if request.method == 'POST':
        form = MesaForm(request.POST, instance=mesa)
        if form.is_valid():
            form.save()
            messages.success(request, f'Mesa {mesa.numMesa} actualizada.')
            return redirect('mesas_lista')
    else:
        form = MesaForm(instance=mesa)
    return render(request, 'core/mesa_editar.html', {'form': form, 'mesa': mesa})


# ─── PLATOS ───────────────────────────────────────────────────────────────────

@rol_requerido('Administrador')
def platos_lista(request):
    platos = Plato.objects.all()
    form = PlatoForm()
    if request.method == 'POST':
        form = PlatoForm(request.POST)
    if form.is_valid():
        
        plato = form.save(commit=False)
        plato.idUsuario = Usuario.objects.get(pk=request.session['usuario_id'])
        plato.save()
        messages.success(request, '¡Plato agregado correctamente!')
        return redirect('platos_lista')
    else:
        print(form.errors)
        messages.error(request, 'Error al agregar el plato.')
    return render(request, 'core/platos.html', {'platos': platos, 'form': form})


@rol_requerido('Administrador')
def plato_eliminar(request, pk):
    plato = get_object_or_404(Plato, pk=pk)
    if request.method == 'POST':
        try:
            plato.delete()
            messages.success(request, f'Plato "{plato.nombre}" eliminado.')
        except Exception:
            messages.error(request, f'No se puede eliminar "{plato.nombre}" porque ya fue usado en pedidos.')
    return redirect('platos_lista')


@rol_requerido('Administrador')
def plato_editar(request, pk):
    plato = get_object_or_404(Plato, pk=pk)
    if request.method == 'POST':
        form = PlatoForm(request.POST, instance=plato)
        if form.is_valid():
            form.save()
            messages.success(request, f'Plato "{plato.nombre}" actualizado.')
            return redirect('platos_lista')
    else:
        form = PlatoForm(instance=plato)
    return render(request, 'core/plato_editar.html', {'form': form, 'plato': plato})


# ─── MENÚS ────────────────────────────────────────────────────────────────────

@rol_requerido('Administrador')
def menus_lista(request):
    menus = Menu.objects.prefetch_related('menu_platos__idPlato').all()
    form = MenuForm()
    platos = Plato.objects.all()
    if request.method == 'POST':
        form = MenuForm(request.POST)
        if form.is_valid():
            menu = form.save()
            platos_ids = request.POST.getlist('platos')
            for plato_id in platos_ids:
                plato = Plato.objects.get(pk=plato_id)
                MenuPlato.objects.create(
                    idMenu=menu, idPlato=plato,
                    nombre=plato.nombre, descripcion=plato.descripcion, precio=plato.precio,
                )
            messages.success(request, '¡Menú agregado correctamente!')
            return redirect('menus_lista')
        else:
            messages.error(request, 'Error al agregar el menú.')
    return render(request, 'core/menus.html', {'menus': menus, 'form': form, 'platos': platos})


@rol_requerido('Administrador')
def menu_eliminar(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    if request.method == 'POST':
        menu.delete()
        messages.success(request, f'Menú "{menu.nombre}" eliminado.')
    return redirect('menus_lista')


@rol_requerido('Administrador')
def menu_editar(request, pk):
    menu = get_object_or_404(Menu, pk=pk)
    platos = Plato.objects.all()
    platos_actuales = menu.menu_platos.values_list('idPlato__pk', flat=True)
    if request.method == 'POST':
        form = MenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            menu.menu_platos.all().delete()
            platos_ids = request.POST.getlist('platos')
            for plato_id in platos_ids:
                plato = Plato.objects.get(pk=plato_id)
                MenuPlato.objects.create(
                    idMenu=menu, idPlato=plato,
                    nombre=plato.nombre, descripcion=plato.descripcion, precio=plato.precio,
                )
            messages.success(request, f'Menú "{menu.nombre}" actualizado.')
            return redirect('menus_lista')
    else:
        form = MenuForm(instance=menu)
    return render(request, 'core/menu_editar.html', {
        'form': form, 'menu': menu, 'platos': platos, 'platos_actuales': list(platos_actuales),
    })


# ─── USUARIOS ─────────────────────────────────────────────────────────────────

@rol_requerido('Administrador')
def usuarios_lista(request):
    usuarios = Usuario.objects.select_related('idRol').all()
    form = UsuarioForm()
    if request.method == 'POST':
        form = UsuarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Usuario agregado correctamente!')
            return redirect('usuarios_lista')
        else:
            messages.error(request, 'Error al agregar el usuario.')
    return render(request, 'core/usuarios.html', {'usuarios': usuarios, 'form': form})


@rol_requerido('Administrador')
def usuario_eliminar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        try:
            usuario.delete()
            messages.success(request, f'Usuario "{usuario.usuario}" eliminado.')
        except Exception:
            messages.error(request, f'No se puede eliminar a "{usuario.usuario}" porque tiene mesas o registros asociados.')
    return redirect('usuarios_lista')

@rol_requerido('Administrador')
def usuario_editar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        form = UsuarioForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario "{usuario.usuario}" actualizado.')
            return redirect('usuarios_lista')
    else:
        form = UsuarioForm(instance=usuario)
    return render(request, 'core/usuario_editar.html', {'form': form, 'usuario': usuario})


# ─── PANEL MESERO ─────────────────────────────────────────────────────────────

@rol_requerido('Administrador', 'Mesero')
def panel_mesero(request):
    mesas = Mesa.objects.select_related('estado').all()
    estado_listo = Estado.objects.filter(descripcion__iexact='listo').first()
    pedidos_listos = Pedido.objects.filter(idEstado=estado_listo).select_related('idMesa') if estado_listo else []
    return render(request, 'core/mesero/panel.html', {
        'mesas': mesas,
        'pedidos_listos': pedidos_listos,
    })


@rol_requerido('Administrador', 'Mesero')
def mesa_pedido(request, pk):
    mesa = get_object_or_404(Mesa, pk=pk)
    platos = Plato.objects.all()
    estados = Estado.objects.filter(descripcion__in=['Disponible', 'Reservada', 'Ocupada'])

    pedido_activo = mesa.pedidos.filter(
        idEstado__descripcion__iexact='pendiente'
    ).first() or mesa.pedidos.filter(
        idEstado__descripcion__iexact='en cocina'
    ).first() or mesa.pedidos.filter(
        idEstado__descripcion__iexact='listo'
    ).first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cambiar_estado':
            nuevo_estado_desc = request.POST.get('estado_mesa')
            estado_obj = Estado.objects.filter(descripcion__iexact=nuevo_estado_desc).first()
            if estado_obj:
                mesa.estado = estado_obj
                mesa.save()
                messages.success(request, f'Estado de Mesa {mesa.numMesa} actualizado.')
            return redirect('mesa_pedido', pk=pk)

        elif action == 'agregar_plato':
            plato_id = request.POST.get('plato_id')
            cantidad = int(request.POST.get('cantidad', 1))
            notas = request.POST.get('notas', '')
            plato = get_object_or_404(Plato, pk=plato_id)

            if not pedido_activo:
                estado_ocupada = Estado.objects.filter(descripcion__iexact='ocupada').first()
                if estado_ocupada:
                    mesa.estado = estado_ocupada
                    mesa.save()
                usuario = Usuario.objects.get(pk=request.session['usuario_id'])
                estado_pendiente = Estado.objects.filter(descripcion__iexact='pendiente').first()
                pedido_activo = Pedido.objects.create(
                    idMesa=mesa,
                    idUsuario=usuario,
                    idEstado=estado_pendiente,
                )

            DetallePedido.objects.create(
                pedido=pedido_activo,
                plato=plato,
                cantidad=cantidad,
                notas=notas,
                precio_unitario=plato.precio,
            )
            pedido_activo.calcular_total()
            messages.success(request, f'"{plato.nombre}" agregado al pedido.')
            return redirect('mesa_pedido', pk=pk)

        elif action == 'eliminar_detalle':
            detalle_id = request.POST.get('detalle_id')
            detalle = get_object_or_404(DetallePedido, pk=detalle_id)
            detalle.delete()
            if pedido_activo:
                pedido_activo.calcular_total()
            messages.success(request, 'Platillo eliminado del pedido.')
            return redirect('mesa_pedido', pk=pk)

        elif action == 'enviar_cocina':
            if pedido_activo:
                estado_cocina = Estado.objects.filter(descripcion__iexact='en cocina').first()
                if estado_cocina:
                    pedido_activo.idEstado = estado_cocina
                    pedido_activo.save()
                messages.success(request, f'¡Pedido de Mesa {mesa.numMesa} enviado a cocina!')
            return redirect('panel_mesero')

        elif action == 'entregar_pedido':
            if pedido_activo:
                estado_entregado = Estado.objects.filter(descripcion__iexact='entregado').first()
                if estado_entregado:
                    pedido_activo.idEstado = estado_entregado
                    pedido_activo.save()
                estado_disponible = Estado.objects.filter(descripcion__iexact='disponible').first()
                if estado_disponible:
                    mesa.estado = estado_disponible
                    mesa.save()
                messages.success(request, f'¡Pedido de Mesa {mesa.numMesa} entregado! Mesa liberada.')
            return redirect('panel_mesero')

    return render(request, 'core/mesero/mesa_pedido.html', {
        'mesa': mesa,
        'platos': platos,
        'pedido': pedido_activo,
        'estados': estados,
    })


# ─── PANEL COCINA ─────────────────────────────────────────────────────────────

@rol_requerido('Administrador', 'Mesero', 'Cocinero')
def panel_cocina(request):
    pedidos = Pedido.objects.filter(idEstado__in=[7, 9]).prefetch_related('detalles__plato').select_related('idMesa')

    if request.method == 'POST':
        pedido_id = request.POST.get('pedido_id')
        accion = request.POST.get('accion')
        pedido = get_object_or_404(Pedido, pk=pedido_id)
        if accion == 'preparando':
            pedido.idEstado = Estado.objects.get(id=9)
            messages.success(request, f'Pedido #{pedido.pk} pasado a En Preparación.')
        elif accion == 'listo':
            pedido.idEstado = Estado.objects.get(id=8)
            messages.success(request, f'Pedido #{pedido.pk} marcado como Listo.')
        elif accion == 'cancelar':
            pedido.idEstado = Estado.objects.get(id=6)
            messages.warning(request, f'Pedido #{pedido.pk} cancelado.')

        pedido.save()
        return redirect('panel_cocina')

    return render(request, 'core/cocina/panel.html', {'pedidos': pedidos})


# ─── PANEL CAJERO ─────────────────────────────────────────────────────────────

@rol_requerido('Administrador', 'Cajero')
def panel_cajero(request):
    hoy = now().date()

    ventas_hoy = Pedido.objects.filter(
        idEstado__descripcion__iexact='entregado',
        fecha__date=hoy
    ).aggregate(total=Sum('total'))['total'] or 0

    total_listos = Pedido.objects.filter(
        idEstado__descripcion__iexact='listo',
        fecha__date=hoy
    ).aggregate(total=Sum('total'))['total'] or 0

    total_para_cobrar = ventas_hoy + total_listos

    ventas_mes = Pedido.objects.filter(
        idEstado__descripcion__iexact='entregado',
        fecha__year=hoy.year,
        fecha__month=hoy.month
    ).aggregate(total=Sum('total'))['total'] or 0

    cierres = CierreCaja.objects.all()[:10]
    cierre_hoy = CierreCaja.objects.filter(fecha=hoy).first()

    if request.method == 'POST':
        efectivo = Decimal(str(request.POST.get('efectivo') or 0))
        electronico = Decimal(str(request.POST.get('electronico') or 0))
        usuario = Usuario.objects.get(pk=request.session['usuario_id'])

        if cierre_hoy:
            cierre_hoy.efectivo = efectivo
            cierre_hoy.electronico = electronico
            cierre_hoy.total_ventas = total_para_cobrar
            cierre_hoy.save()
            messages.success(request, f'Cierre del día actualizado. Total: ${cierre_hoy.total():,.0f}')
        else:
            cierre = CierreCaja.objects.create(
                efectivo=efectivo,
                electronico=electronico,
                total_ventas=total_para_cobrar,
                registrado_por=usuario,
            )
            messages.success(request, f'¡Cierre del día registrado! Total: ${cierre.total():,.0f}')

        return redirect('panel_cajero')

    return render(request, 'core/cajero/panel.html', {
        'ventas_hoy': ventas_hoy,
        'total_listos': total_listos,
        'total_para_cobrar': total_para_cobrar,
        'ventas_mes': ventas_mes,
        'cierres': cierres,
        'cierre_hoy': cierre_hoy,
        'hoy': hoy,
    })


@rol_requerido('Administrador', 'Cajero')
def historial_cierres(request):
    hoy = now().date()
    mes = request.GET.get('mes', hoy.month)
    anio = request.GET.get('anio', hoy.year)

    cierres = CierreCaja.objects.filter(
        fecha__year=anio,
        fecha__month=mes
    ).select_related('registrado_por')

    total_mes_efectivo = sum(c.efectivo for c in cierres)
    total_mes_electronico = sum(c.electronico for c in cierres)
    total_mes = total_mes_efectivo + total_mes_electronico

    return render(request, 'core/cajero/historial.html', {
        'cierres': cierres,
        'mes': int(mes),
        'anio': int(anio),
        'total_mes_efectivo': total_mes_efectivo,
        'total_mes_electronico': total_mes_electronico,
        'total_mes': total_mes,
    })


# ─── REPORTES ─────────────────────────────────────────────────────────────────

@rol_requerido('Administrador')
def reportes(request):
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    pedidos_entregados = Pedido.objects.filter(
        idEstado__descripcion__iexact='entregado'
    ).select_related('idMesa', 'idUsuario').prefetch_related('detalles__plato')

    pedidos_hoy = pedidos_entregados.filter(fecha__date=hoy)
    total_hoy = sum(p.total for p in pedidos_hoy)

    pedidos_semana = pedidos_entregados.filter(fecha__date__gte=inicio_semana)
    total_semana = sum(p.total for p in pedidos_semana)

    pedidos_mes = pedidos_entregados.filter(fecha__date__gte=inicio_mes)
    total_mes = sum(p.total for p in pedidos_mes)

    meseros = Usuario.objects.filter(idRol__descripcion__iexact='mesero')
    reporte_camareros = []
    for mesero in meseros:
        pedidos_mesero = pedidos_entregados.filter(idUsuario=mesero, fecha__date=hoy)
        mesas = pedidos_mesero.values('idMesa').distinct().count()
        total = sum(p.total for p in pedidos_mesero)
        reporte_camareros.append({
            'nombre': f"{mesero.nombre} {mesero.apellido}",
            'mesas': mesas,
            'pedidos': pedidos_mesero.count(),
            'total': total,
        })

    return render(request, 'core/reportes.html', {
        'hoy': hoy,
        'pedidos_hoy': pedidos_hoy,
        'total_hoy': total_hoy,
        'pedidos_semana': pedidos_semana,
        'total_semana': total_semana,
        'pedidos_mes': pedidos_mes,
        'total_mes': total_mes,
        'reporte_camareros': reporte_camareros,
        'inicio_semana': inicio_semana,
        'inicio_mes': inicio_mes,
    })
# ─── ESTADÍSTICAS MESERO ──────────────────────────────────────────────────────

@rol_requerido('Administrador', 'Mesero')
def estadisticas_mesero(request):
    hoy = date.today()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_mes = hoy.replace(day=1)

    usuario_id = request.session.get('usuario_id')
    usuario = get_object_or_404(Usuario, pk=usuario_id)

    pedidos_propios = Pedido.objects.filter(
        idUsuario=usuario,
        idEstado__descripcion__iexact='entregado'
    ).select_related('idMesa').prefetch_related('detalles__plato')

    # Período seleccionado
    periodo = request.GET.get('periodo', 'diario')

    if periodo == 'semanal':
        pedidos_periodo = pedidos_propios.filter(fecha__date__gte=inicio_semana)
        label_periodo = f"Semana del {inicio_semana.strftime('%d/%m')} al {hoy.strftime('%d/%m/%Y')}"
    elif periodo == 'mensual':
        pedidos_periodo = pedidos_propios.filter(fecha__date__gte=inicio_mes)
        label_periodo = f"Mes de {hoy.strftime('%B %Y')}"
    else:
        pedidos_periodo = pedidos_propios.filter(fecha__date=hoy)
        label_periodo = f"Hoy {hoy.strftime('%d/%m/%Y')}"

    total_periodo = sum(p.total for p in pedidos_periodo)
    mesas_periodo = pedidos_periodo.values('idMesa').distinct().count()

    return render(request, 'core/mesero/estadisticas.html', {
        'usuario': usuario,
        'periodo': periodo,
        'label_periodo': label_periodo,
        'pedidos_periodo': pedidos_periodo,
        'total_periodo': total_periodo,
        'mesas_periodo': mesas_periodo,
        'hoy': hoy,
    })
