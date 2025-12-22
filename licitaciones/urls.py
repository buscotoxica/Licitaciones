from django.urls import path
from django.contrib import admin
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('administracion/', views.vista_admin, name='vista_admin'),
    path('operador/', views.vista_operador, name='vista_operador'),
    path('vizualizador/', views.vista_vizualizador, name='vista_vizualizador'),

    path('estadisticas/', views.estadisticas_view, name='estadisticas'),
    path('calendario/', views.calendario_actividad, name='calendario_actividad'),
    path('', views.gestion_licitaciones, name='gestion_licitaciones'),
    path('gestion/modificar_licitacion/<int:licitacion_id>/', views.modificar_licitacion, name='modificar_licitacion'),
    path('gestion/eliminar_licitacion/<int:licitacion_id>/', views.eliminar_licitacion, name='eliminar_licitacion'),
    path('api/fecha_creacion/<int:licitacion_id>/', views.fecha_creacion_api, name='fecha_creacion_api'),
    path('licitaciones-operador/', views.licitaciones_operador, name='licitaciones_operador'),
    path('operador-manual/', views.vista_operador_manual, name='vista_operador_manual'),
    path('bitacora/<int:licitacion_id>/', views.bitacora_licitacion, name='bitacora_licitacion'),
    path('api/licitacion/<int:licitacion_id>/documentos/subir/', views.subir_documentos_licitacion, name='subir_documentos_licitacion'),
    path('api/licitacion/<int:licitacion_id>/documentos/', views.listar_documentos_licitacion, name='listar_documentos_licitacion'),
    path('api/licitacion/<int:licitacion_id>/etapa/', views.etapa_actual_api, name='etapa_actual_api'),
    path('api/licitacion/<int:licitacion_id>/etapas/', views.etapas_licitacion_api, name='etapas_licitacion_api'),
    path('api/licitacion/<int:licitacion_id>/documentos/<int:doc_id>/eliminar/', views.eliminar_documento_licitacion, name='eliminar_documento_licitacion'),
    path('api/licitacion/<int:licitacion_id>/observacion/', views.guardar_observacion_operador, name='guardar_observacion_operador'),
    path('api/licitacion/<int:licitacion_id>/cerrar/', views.cerrar_licitacion_operador, name='cerrar_licitacion_operador'),
    path('api/bitacora/<int:bitacora_id>/observacion/', views.observacion_bitacora_api, name='observacion_bitacora_api'),
    path('gestion/agregar_proyecto/', views.agregar_proyecto, name='agregar_proyecto'),
    path('bitacora/eliminar/<int:bitacora_id>/', views.eliminar_bitacora, name='eliminar_bitacora'),
    path('api/licitacion/<int:licitacion_id>/exportar_excel/', views.exportar_licitacion_excel, name='exportar_licitacion_excel'),
    path('api/exportar_todas_licitaciones_excel/', views.exportar_todas_licitaciones_excel, name='exportar_todas_licitaciones_excel'),
    path('api/validar_numero_pedido/', views.api_validar_numero_pedido, name='api_validar_numero_pedido'),
    path('api/licitacion/<int:licitacion_id>/ultima_observacion/', views.api_ultima_observacion, name='api_ultima_observacion'),
    path('api/licitacion/<int:licitacion_id>/puede_retroceder/', views.api_puede_retroceder_etapa, name='api_puede_retroceder_etapa'),
    path('api/licitacion/<int:licitacion_id>/puede_avanzar/', views.api_puede_avanzar_etapa, name='api_puede_avanzar_etapa'),
    path('api/licitaciones/fallidas/', views.api_licitaciones_fallidas, name='api_licitaciones_fallidas'),
    path('api/licitacion/linkear-fallida/', views.api_linkear_licitacion_fallida, name='api_linkear_licitacion_fallida'),
    path('api/licitacion/<int:licitacion_id>/actualizar_etapa/', views.actualizar_etapa_api, name='actualizar_etapa_api'),
    # Rutas para notificaciones
    path('api/notificaciones/', views.obtener_notificaciones_api, name='obtener_notificaciones_api'),
    path('api/notificaciones/<int:notificacion_id>/marcar_leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('api/notificaciones/marcar_todas_leidas/', views.marcar_todas_notificaciones_leidas, name='marcar_todas_notificaciones_leidas'),
    # Ruta para calendario
    path('api/calendario/eventos/', views.obtener_eventos_calendario, name='obtener_eventos_calendario'),
    path('ajax/crear-departamento/', views.crear_departamento_ajax, name='crear_departamento_ajax'),
    path("api/licitacion/<int:licitacion_id>/info-general/",views.licitacion_info_general,name="licitacion_info_general"),
]