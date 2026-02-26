from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('recuperar-contrasena/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('acceso-denegado/', views.acceso_denegado, name='acceso_denegado'),

    # Mesas
    path('mesas/', views.mesas_lista, name='mesas_lista'),
    path('mesas/eliminar/<int:pk>/', views.mesa_eliminar, name='mesa_eliminar'),
    path('mesas/editar/<int:pk>/', views.mesa_editar, name='mesa_editar'),

    # Platos
    path('platos/', views.platos_lista, name='platos_lista'),
    path('platos/eliminar/<int:pk>/', views.plato_eliminar, name='plato_eliminar'),
    path('platos/editar/<int:pk>/', views.plato_editar, name='plato_editar'),

    # Menús
    path('menus/', views.menus_lista, name='menus_lista'),
    path('menus/eliminar/<int:pk>/', views.menu_eliminar, name='menu_eliminar'),
    path('menus/editar/<int:pk>/', views.menu_editar, name='menu_editar'),

    # Usuarios
    path('usuarios/', views.usuarios_lista, name='usuarios_lista'),
    path('usuarios/eliminar/<int:pk>/', views.usuario_eliminar, name='usuario_eliminar'),
    path('usuarios/editar/<int:pk>/', views.usuario_editar, name='usuario_editar'),

    # Mesero
    path('mesero/', views.panel_mesero, name='panel_mesero'),
    path('mesero/mesa/<int:pk>/', views.mesa_pedido, name='mesa_pedido'),
    path('mesero/estadisticas/', views.estadisticas_mesero, name='estadisticas_mesero'),

    # Cocina
    path('cocina/', views.panel_cocina, name='panel_cocina'),

    # Cajero
    path('cajero/', views.panel_cajero, name='panel_cajero'),
    path('cajero/historial/', views.historial_cierres, name='historial_cierres'),

    # Reportes
    path('reportes/', views.reportes, name='reportes'),
]
