"""
SISTEMA DE GESTIÓN DE LICITACIONES MUNICIPALES
===============================================

Archivo: views.py - Vistas principales del sistema
Desarrollador Principal: [Tu Nombre Aquí]
Email: [tu.email@ejemplo.com]
Período de Desarrollo: 2024-2025

Este archivo contiene todas las vistas (views) del sistema de gestión de licitaciones,
incluyendo la lógica de negocio, validaciones, APIs y funcionalidades avanzadas.

Características implementadas:
- Sistema completo de CRUD para licitaciones
- API endpoints para validaciones en tiempo real
- Gestión de archivos con drag & drop
- Sistema de roles (Admin/Operador) con permisos granulares
- Exportación avanzada a Excel
- Bitácora detallada de actividades
- Cronología visual de etapas
- Y muchas más funcionalidades...

Para información detallada sobre el desarrollo, consultar CONTRIBUTORS.md
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User
from django.db.models import Count, F
from django.utils import timezone
from django.views.decorators.http import require_POST, require_GET, require_http_methods
from django.contrib import messages
import json
import io
import pandas as pd
from .utils import *
from datetime import datetime
from .models import Licitacion, Etapa, BitacoraLicitacion, Estado, DocumentoLicitacion, TipoLicitacion, Moneda, Categoria, Financiamiento, ObservacionBitacora, Departamento, DocumentoObservacion, Notificacion
from .models import TipoLicitacionEtapa
from django.db import models
from django.http import JsonResponse
from django.db.models import Q


@login_required
def gestion_licitaciones(request):
    # Si el usuario es admin, redirige a vista_admin; si es operador, a vista_operador
    perfil = getattr(request.user, 'perfil', None)
    if perfil and (perfil.rol or '').strip().lower() == 'operador':
        return redirect('vista_operador')
    return redirect('vista_admin')

@csrf_exempt
def modificar_licitacion(request, licitacion_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        licitacion = Licitacion.objects.get(id=licitacion_id)
        cambios = []
        campos_modificados = []
        valores_antes = {}
        valores_despues = {}
        texto_bitacora = ""
        # Solo actualizar el operador si solo viene ese campo
        if ('operador' in data or 'operador_id' in data) and len(data) == 1:
            operador_id = data.get('operador') or data.get('operador_id')
            operador_user = User.objects.get(id=operador_id) if operador_id else None
            if licitacion.operador_user != operador_user:
                cambios.append(f"Operador: '{licitacion.operador_user}' → '{operador_user}'")
                campos_modificados.append('Operador')
                valores_antes['Operador'] = str(licitacion.operador_user)
                valores_despues['Operador'] = str(operador_user)
            licitacion.operador_user = operador_user
            licitacion.save()
        # Solo actualizar la etapa si solo viene ese campo
        elif 'etapa' in data and len(data) == 1:
            etapa_id = data.get('etapa')
            etapa_obj = Etapa.objects.get(id=etapa_id) if etapa_id else None
            if licitacion.etapa_fk != etapa_obj:
                cambios.append(f"Etapa: '{licitacion.etapa_fk}' → '{etapa_obj}'")
                campos_modificados.append('Etapa')
                valores_antes['Etapa'] = str(licitacion.etapa_fk)
                valores_despues['Etapa'] = str(etapa_obj)
            licitacion.etapa_fk = etapa_obj
            licitacion.save()
        # Solo actualizar el estado si solo viene ese campo
        elif 'estado' in data and len(data) == 1:
            estado_id = data.get('estado')
            estado_obj = Estado.objects.get(id=estado_id) if estado_id else None
            if licitacion.estado_fk != estado_obj:
                cambios.append(f"Estado: '{licitacion.estado_fk}' → '{estado_obj}'")
                # Si el nuevo estado es "En curso" y la licitación estaba cerrada, reabrirla
                if estado_obj.nombre.strip().lower() == 'en curso':
                    texto_bitacora = "🔓 LICITACIÓN REABIERTA\n\n"
                    if licitacion.tipo_fallida is not None:
                        texto_bitacora += f"Se elimina el estado de licitación fallida '{licitacion.tipo_fallida}'.\n\n"
                        licitacion.tipo_fallida = None
                campos_modificados.append('Estado')
                valores_antes['Estado'] = str(licitacion.estado_fk)
                valores_despues['Estado'] = str(estado_obj)
            licitacion.estado_fk = estado_obj
            licitacion.save()
        else:
            operador_id = data.get('operador') or data.get('operador_id')
            operador_user = User.objects.get(id=operador_id) if operador_id else None
            if licitacion.operador_user != operador_user:
                cambios.append(f"Operador 1: '{licitacion.operador_user}' → '{operador_user}'")
                campos_modificados.append('Operador 1')
                valores_antes['Operador 1'] = str(licitacion.operador_user)
                valores_despues['Operador 1'] = str(operador_user)
            
            # Manejar operador 2
            operador_2_id = data.get('operador_2')
            operador_2_user = User.objects.get(id=operador_2_id) if operador_2_id else None
            if licitacion.operador_2 != operador_2_user:
                cambios.append(f"Operador 2: '{licitacion.operador_2}' → '{operador_2_user}'")
                campos_modificados.append('Operador 2')
                valores_antes['Operador 2'] = str(licitacion.operador_2)
                valores_despues['Operador 2'] = str(operador_2_user)
            
            iniciativa = data.get('iniciativa', '')
            if licitacion.iniciativa != iniciativa:
                cambios.append(f"Iniciativa: '{licitacion.iniciativa}' → '{iniciativa}'")
                campos_modificados.append('Iniciativa')
                valores_antes['Iniciativa'] = str(licitacion.iniciativa)
                valores_despues['Iniciativa'] = str(iniciativa)
            etapa_id = data.get('etapa')
            etapa_obj = Etapa.objects.get(id=etapa_id) if etapa_id else None
            if licitacion.etapa_fk != etapa_obj:
                cambios.append(f"Etapa: '{licitacion.etapa_fk}' → '{etapa_obj}'")
                campos_modificados.append('Etapa')
                valores_antes['Etapa'] = str(licitacion.etapa_fk)
                valores_despues['Etapa'] = str(etapa_obj)
            # Estado
            estado_obj = licitacion.estado_fk  # Siempre inicializado con el valor actual
            if 'estado' in data:
                estado_id = data.get('estado')
                if estado_id:
                    estado_obj = Estado.objects.get(id=estado_id)
                    if licitacion.estado_fk != estado_obj:
                        cambios.append(f"Estado: '{licitacion.estado_fk}' → '{estado_obj}'")
                        campos_modificados.append('Estado')
                        valores_antes['Estado'] = str(licitacion.estado_fk)
                        valores_despues['Estado'] = str(estado_obj)
                licitacion.estado_fk = estado_obj
            # Departamento
            departamento_id = data.get('departamento')
            departamento_obj = None
            if departamento_id:
                try:
                    departamento_obj = Departamento.objects.get(id=departamento_id)
                except Departamento.DoesNotExist:
                    departamento_obj = None
            if licitacion.departamento != departamento_obj:
                cambios.append(f"Departamento: '{licitacion.departamento}' → '{departamento_obj}'")
                campos_modificados.append('Departamento')
                valores_antes['Departamento'] = str(licitacion.departamento)
                valores_despues['Departamento'] = str(departamento_obj)
            # Monto presupuestado - convertir de forma segura
            monto_presupuestado_input = data.get('monto_presupuestado') or 0
            try:
                monto_actual = float(licitacion.monto_presupuestado)
                monto_nuevo = float(monto_presupuestado_input)
                # Convertir a número para asignar al modelo
                monto_presupuestado = monto_nuevo
            except (ValueError, TypeError):
                # Si no se puede convertir, mantener como está o usar 0
                monto_actual = float(licitacion.monto_presupuestado) if licitacion.monto_presupuestado else 0
                try:
                    monto_nuevo = float(monto_presupuestado_input)
                    monto_presupuestado = monto_nuevo
                except (ValueError, TypeError):
                    monto_nuevo = 0
                    monto_presupuestado = 0
            if monto_actual != monto_nuevo:
                cambios.append(f"Monto Presupuestado: '{licitacion.monto_presupuestado}' → '{monto_presupuestado}'")
                campos_modificados.append('Monto Presupuestado')
                valores_antes['Monto Presupuestado'] = str(licitacion.monto_presupuestado)
                valores_despues['Monto Presupuestado'] = str(monto_presupuestado)
            # --- en_plan_anual ---
            if 'en_plan_anual' in data:
                en_plan_anual = data.get('en_plan_anual', False)
                if isinstance(en_plan_anual, str):
                    en_plan_anual = en_plan_anual.lower() in ['1', 'true', 'sí', 'si']
                elif isinstance(en_plan_anual, int):
                    en_plan_anual = bool(en_plan_anual)
                if licitacion.en_plan_anual != en_plan_anual:
                    cambios.append(f"En plan anual: '{licitacion.en_plan_anual}' → '{en_plan_anual}'")
                    campos_modificados.append('En plan anual')
                    valores_antes['En plan anual'] = str(licitacion.en_plan_anual)
                    valores_despues['En plan anual'] = str(en_plan_anual)
                licitacion.en_plan_anual = en_plan_anual
            if licitacion.en_plan_anual != en_plan_anual:
                cambios.append(f"En plan anual: '{licitacion.en_plan_anual}' → '{en_plan_anual}'")
                campos_modificados.append('En plan anual')
                valores_antes['En plan anual'] = str(licitacion.en_plan_anual)
                valores_despues['En plan anual'] = str(en_plan_anual)
            licitacion.en_plan_anual = en_plan_anual

            # 👇👇 AGREGA ESTO JUSTO AQUÍ 👇👇
            
            # --- Justificación Plan Anual ---
            justificacion_plan = data.get('justificacion_plan', '')
            
            # Aseguramos que no sea None para comparar strings
            val_antiguo = licitacion.justificacion_plan if licitacion.justificacion_plan else ""
            val_nuevo = justificacion_plan if justificacion_plan else ""

            if val_antiguo != val_nuevo:
                cambios.append(f"Justificación Plan: '{val_antiguo}' → '{val_nuevo}'")
                campos_modificados.append('Justificación Plan')
                valores_antes['Justificación Plan'] = val_antiguo
                valores_despues['Justificación Plan'] = val_nuevo
                
                licitacion.justificacion_plan = val_nuevo
            # --- pedido_devuelto ---
            if 'pedido_devuelto' in data:
                pedido_devuelto = data.get('pedido_devuelto', False)
                if isinstance(pedido_devuelto, str):
                    pedido_devuelto = pedido_devuelto.lower() in ['1', 'true', 'sí', 'si']
                elif isinstance(pedido_devuelto, int):
                    pedido_devuelto = bool(pedido_devuelto)
                if licitacion.pedido_devuelto != pedido_devuelto:
                    cambios.append(f"Pedido devuelto: '{licitacion.pedido_devuelto}' → '{pedido_devuelto}'")
                    campos_modificados.append('Pedido devuelto')
                    valores_antes['Pedido devuelto'] = str(licitacion.pedido_devuelto)
                    valores_despues['Pedido devuelto'] = str(pedido_devuelto)
                licitacion.pedido_devuelto = pedido_devuelto
            licitacion.operador_user = operador_user
            licitacion.operador_2 = operador_2_user
            licitacion.iniciativa = iniciativa
            licitacion.etapa_fk = etapa_obj
            licitacion.estado_fk = estado_obj
            licitacion.departamento = departamento_obj
            licitacion.monto_presupuestado = monto_presupuestado
            licitacion.llamado_cotizacion = data.get('llamado_cotizacion', '')
            # Moneda
            moneda_id = data.get('moneda')
            moneda_obj = Moneda.objects.get(id=moneda_id) if moneda_id else None
            if licitacion.moneda != moneda_obj:
                cambios.append(f"Moneda: '{licitacion.moneda}' → '{moneda_obj}'")
                campos_modificados.append('Moneda')
                valores_antes['Moneda'] = str(licitacion.moneda)
                valores_despues['Moneda'] = str(moneda_obj)
            licitacion.moneda = moneda_obj
            # Categoría
            categoria_id = data.get('categoria')
            categoria_obj = Categoria.objects.get(id=categoria_id) if categoria_id else None
            if licitacion.categoria != categoria_obj:
                cambios.append(f"Categoría: '{licitacion.categoria}' → '{categoria_obj}'")
                campos_modificados.append('Categoría')
                valores_antes['Categoría'] = str(licitacion.categoria)
                valores_despues['Categoría'] = str(categoria_obj)
            licitacion.categoria = categoria_obj
            # Financiamiento
            financiamiento_ids = data.get('financiamiento', [])
            if isinstance(financiamiento_ids, list):
                financiamiento_objs = Financiamiento.objects.filter(id__in=financiamiento_ids)
                current_financiamiento_ids = set(licitacion.financiamiento.values_list('id', flat=True))
                new_financiamiento_ids = set(financiamiento_objs.values_list('id', flat=True))

                if current_financiamiento_ids != new_financiamiento_ids:
                    cambios.append(f"Financiamiento: '{current_financiamiento_ids}' → '{new_financiamiento_ids}'")
                    campos_modificados.append('Financiamiento')
                    valores_antes['Financiamiento'] = str(current_financiamiento_ids)
                    valores_despues['Financiamiento'] = str(new_financiamiento_ids)

                licitacion.financiamiento.set(financiamiento_objs)
            else:
                financiamiento_obj = Financiamiento.objects.get(id=financiamiento_ids) if financiamiento_ids else None
                if licitacion.financiamiento != financiamiento_obj:
                    cambios.append(f"Financiamiento: '{licitacion.financiamiento}' → '{financiamiento_obj}'")
                    campos_modificados.append('Financiamiento')
                    valores_antes['Financiamiento'] = str(licitacion.financiamiento)
                    valores_despues['Financiamiento'] = str(financiamiento_obj)
                licitacion.financiamiento = financiamiento_obj
            # Número de pedido
            numero_pedido = data.get('numero_pedido')
            if numero_pedido is not None and str(licitacion.numero_pedido) != str(numero_pedido):
                cambios.append(f"N° de pedido: '{licitacion.numero_pedido}' → '{numero_pedido}'")
                campos_modificados.append('N° de pedido')
                valores_antes['N° de pedido'] = str(licitacion.numero_pedido)
                valores_despues['N° de pedido'] = str(numero_pedido)
                licitacion.numero_pedido = numero_pedido

            #  ⬇️ AGREGAR ESTO: Lógica para Profesional a Cargo ⬇️
            profesional_nuevo = data.get('profesional_a_cargo')
            
            # Comparamos para guardar en la bitácora si cambió
            if profesional_nuevo is not None and str(licitacion.profesional_a_cargo or '') != str(profesional_nuevo):
                cambios.append(f"Profesional a Cargo: '{licitacion.profesional_a_cargo or ''}' → '{profesional_nuevo}'")
                campos_modificados.append('Profesional a Cargo')
                valores_antes['Profesional a Cargo'] = str(licitacion.profesional_a_cargo or '')
                valores_despues['Profesional a Cargo'] = str(profesional_nuevo)
                
                # Asignar el valor
                licitacion.profesional_a_cargo = profesional_nuevo
            # ID Mercado Público
            id_mercado_publico = data.get('id_mercado_publico', '')
            if licitacion.id_mercado_publico != id_mercado_publico:
                cambios.append(f"ID Mercado Público: '{licitacion.id_mercado_publico or '-'}' → '{id_mercado_publico or '-'}'")
                campos_modificados.append('ID Mercado Público')
                valores_antes['ID Mercado Público'] = str(licitacion.id_mercado_publico or '-')
                valores_despues['ID Mercado Público'] = str(id_mercado_publico or '-')
                licitacion.id_mercado_publico = id_mercado_publico
            
            # Número de cuenta
            numero_cuenta = data.get('numero_cuenta', '')
            if licitacion.numero_cuenta != numero_cuenta:
                cambios.append(f"N° de cuenta: '{licitacion.numero_cuenta}' → '{numero_cuenta}'")
                campos_modificados.append('N° de cuenta')
                valores_antes['N° de cuenta'] = str(licitacion.numero_cuenta)
                valores_despues['N° de cuenta'] = str(numero_cuenta)
                licitacion.numero_cuenta = numero_cuenta
            # Tipo de licitación
            tipo_licitacion_id = data.get('tipo_licitacion')
            tipo_licitacion_obj = TipoLicitacion.objects.get(id=tipo_licitacion_id) if tipo_licitacion_id else None
            if tipo_licitacion_obj and licitacion.tipo_licitacion != tipo_licitacion_obj:
                cambios.append(f"Tipo de licitación: '{licitacion.tipo_licitacion}' → '{tipo_licitacion_obj}'")
                campos_modificados.append('Tipo de licitación')
                valores_antes['Tipo de licitación'] = str(licitacion.tipo_licitacion)
                valores_despues['Tipo de licitación'] = str(tipo_licitacion_obj)
                licitacion.tipo_licitacion = tipo_licitacion_obj
            # Llamado cotización
            llamado_cotizacion = data.get('llamado_cotizacion', '')
            if licitacion.llamado_cotizacion != llamado_cotizacion:
                cambios.append(f"Llamado Cotización: '{licitacion.llamado_cotizacion}' → '{llamado_cotizacion}'")
                campos_modificados.append('Llamado Cotización')
                valores_antes['Llamado Cotización'] = str(licitacion.llamado_cotizacion)
                valores_despues['Llamado Cotización'] = str(llamado_cotizacion)
                licitacion.llamado_cotizacion = llamado_cotizacion
            # Dirección
            direccion = data.get('direccion', '')
            if licitacion.direccion != direccion:
                cambios.append(f"Dirección: '{licitacion.direccion}' → '{direccion}'")
                campos_modificados.append('Dirección')
                valores_antes['Dirección'] = str(licitacion.direccion or '')
                valores_despues['Dirección'] = str(direccion)
                licitacion.direccion = direccion
            # Institución
            institucion = data.get('institucion', '')
            if licitacion.institucion != institucion:
                cambios.append(f"Institución: '{licitacion.institucion}' → '{institucion}'")
                campos_modificados.append('Institución')
                valores_antes['Institución'] = str(licitacion.institucion or '')
                valores_despues['Institución'] = str(institucion)
                licitacion.institucion = institucion
            # Tipo por presupuesto
            #tipo_presupuesto = get_tipo_presupuesto(moneda_obj.nombre, monto_presupuestado)
            tipo_presupuesto = data.get('tipo_presupuesto', '')
            if licitacion.tipo_presupuesto != tipo_presupuesto:
                cambios.append(f"Tipo por presupuesto: '{licitacion.tipo_presupuesto}' → '{tipo_presupuesto}'")
                campos_modificados.append('N° de cuenta')
                valores_antes['N° de cuenta'] = str(licitacion.tipo_presupuesto)
                valores_despues['N° de cuenta'] = str(tipo_presupuesto)
                licitacion.tipo_presupuesto = tipo_presupuesto

            fecha_creacion_str = data.get('fecha_creacion')
            if fecha_creacion_str:
                from datetime import datetime
                from django.utils import timezone
                
                # Convertimos el string "YYYY-MM-DD" a objeto datetime
                try:
                    # Parseamos la fecha que viene del input date
                    fecha_nueva_date = datetime.strptime(fecha_creacion_str, '%Y-%m-%d').date()
                    
                    # Como el modelo es DateTimeField, necesitamos combinar con hora (00:00:00)
                    # o mantener la hora que ya tenía si quieres ser muy preciso, 
                    # pero para "Fecha Asignación" suele bastar resetear la hora.
                    fecha_nueva_dt = datetime.combine(fecha_nueva_date, datetime.min.time())
                    
                    # Hacemos la fecha "aware" (con zona horaria) si Django lo requiere
                    if timezone.is_naive(fecha_nueva_dt):
                        fecha_nueva_dt = timezone.make_aware(fecha_nueva_dt)

                    # Comparamos (usamos .date() para comparar solo el día y evitar ruido por horas)
                    if licitacion.fecha_creacion.date() != fecha_nueva_dt.date():
                        fecha_antes_str = licitacion.fecha_creacion.strftime('%d-%m-%Y')
                        fecha_nueva_fmt = fecha_nueva_dt.strftime('%d-%m-%Y')
                        
                        cambios.append(f"Fecha Asignación: '{fecha_antes_str}' → '{fecha_nueva_fmt}'")
                        campos_modificados.append('Fecha Asignación')
                        valores_antes['Fecha Asignación'] = fecha_antes_str
                        valores_despues['Fecha Asignación'] = fecha_nueva_fmt
                        
                        licitacion.fecha_creacion = fecha_nueva_dt
                except ValueError:
                    pass # Si la fecha viene vacía o mal formada, la ignoramos
            fecha_tentativa_termino = get_fecha_tentativa_termino(data.get('tipo_presupuesto', ''), licitacion.fecha_creacion.date())
            if licitacion.fecha_tentativa_termino != fecha_tentativa_termino:
                if (licitacion.fecha_tentativa_termino):
                    cambios.append(f"Fecha tentativa de término: '{str(licitacion.fecha_tentativa_termino.strftime('%d-%m-%Y'))}' → '{str(fecha_tentativa_termino)}'")
                    valores_antes['Fecha tentativa de término'] = str(licitacion.fecha_tentativa_termino.strftime('%d-%m-%Y'))
                campos_modificados.append('Fecha tentativa de término')
                valores_despues['Fecha tentativa de término'] = str(fecha_tentativa_termino)
                licitacion.fecha_tentativa_termino = fecha_tentativa_termino
            # Licitacion fallida linkeada
            licitacion_fallida_linkeada_id = data.get('licitacion_fallida_linkeada')

# Obtener el objeto nuevo o None
            licitacion_fallida_linkeada_obj = Licitacion.objects.get(id=licitacion_fallida_linkeada_id) if licitacion_fallida_linkeada_id else None

# Verificamos si hubo algún cambio (ya sea poner una nueva, cambiarla o quitarla)
            if licitacion.licitacion_fallida_linkeada != licitacion_fallida_linkeada_obj:
    
    # 1. Obtenemos el valor ANTERIOR de forma segura
                valor_anterior = licitacion.licitacion_fallida_linkeada.numero_pedido if licitacion.licitacion_fallida_linkeada else "Ninguna"
    
    # 2. Obtenemos el valor NUEVO de forma segura
                valor_nuevo = licitacion_fallida_linkeada_obj.numero_pedido if licitacion_fallida_linkeada_obj else "Ninguna"

    # 3. Registramos los cambios usando las variables seguras
                cambios.append(f"Licitación fallida linkeada: '{valor_anterior}' → '{valor_nuevo}'")
                campos_modificados.append('Licitación fallida linkeada')
                valores_antes['Licitación fallida linkeada'] = str(valor_anterior)
                valores_despues['Licitación fallida linkeada'] = str(valor_nuevo)

# Asignar y guardar
            licitacion.licitacion_fallida_linkeada = licitacion_fallida_linkeada_obj
            licitacion.save()
            
        # Registrar en bitácora si hubo cambios
        if cambios:
            texto_bitacora += "Campos modificados:" + ''.join([
                f"\n- {campo}: '{valores_antes[campo]}' → '{valores_despues[campo]}'"
                for campo in campos_modificados
            ])
            # Financiamiento changes
            if 'Financiamiento' in campos_modificados:
                # 1. Función auxiliar para limpiar el formato string de set "{1, 2}" a lista [1, 2]
                def limpiar_ids(texto_set):
                    if not texto_set: return []
                    # Quitamos llaves y comillas, luego separamos por comas
                    limpio = texto_set.replace('{', '').replace('}', '').replace("'", "")
                    return [int(x) for x in limpio.split(',') if x.strip().isdigit()]

                # 2. Convertimos el texto guardado de vuelta a listas de números
                ids_antes = limpiar_ids(valores_antes['Financiamiento'])
                ids_despues = limpiar_ids(valores_despues['Financiamiento'])

                # 3. Consultamos usando las listas limpias
                financiamiento_antes = ', '.join(
                    [f.nombre for f in Financiamiento.objects.filter(id__in=ids_antes)]
                )
                financiamiento_despues = ', '.join(
                    [f.nombre for f in Financiamiento.objects.filter(id__in=ids_despues)]
                )
                texto_bitacora += f"\n- Financiamiento: '{financiamiento_antes}' → '{financiamiento_despues}'"
            # --- FIN DE LA CORRECCIÓN ---

            BitacoraLicitacion.objects.create(
                licitacion=licitacion,
                texto=texto_bitacora,
                etapa=licitacion.etapa_fk
            )
            
        return JsonResponse({'ok': True, 'monto_presupuestado': str(licitacion.monto_presupuestado)})
    return JsonResponse({'ok': False}, status=400)

@login_required
@csrf_exempt
def eliminar_licitacion(request, licitacion_id):
    if request.method == 'POST':
        Licitacion.objects.filter(id=licitacion_id).delete()
        return JsonResponse({'ok': True})
    return JsonResponse({'ok': False}, status=400)

def fecha_creacion_api(request, licitacion_id):
    licitacion = Licitacion.objects.get(id=licitacion_id)
    fecha = licitacion.fecha_creacion
    # Formato: 14/05/2025 16:23
    fecha_formateada = fecha.strftime('%d/%m/%Y %H:%M')
    return JsonResponse({'fecha_creacion_formateada': fecha_formateada})

@login_required
def vista_admin(request):
    # Verificar que el usuario es un administrador
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or (perfil.rol or '').strip().lower() != 'admin':
        return redirect('login')
    # Obtener todas las licitaciones ordenadas por ID descendente
    proyectos_list = Licitacion.objects.select_related(
        'operador_user', 'operador_2', 'etapa_fk', 'estado_fk', 'tipo_licitacion',
        'moneda', 'categoria', 'departamento', 'licitacion_fallida_linkeada'
    ).prefetch_related('financiamiento').order_by('-id')

    # Aplicar filtros comunes (fallidas, anuales, búsqueda)
    proyectos_list = get_filtered_projects_list(proyectos_list, request)
    
    # Paginar resultados
    proyectos = get_paginated_projects(proyectos_list, request)
    
    # Obtener todos los catálogos de datos
    catalogs = get_catalog_data()
    
    # Construir el contexto para la plantilla
    context = {
        'proyectos': proyectos,
        'paginator': proyectos.paginator,
        'operadores': User.objects.filter(perfil__rol__in=['operador', 'admin']),
        'es_admin': True,
        **catalogs  # Incluir todos los catálogos
    }
    
    return render(request, 'licitaciones/gestion_licitaciones.html', context)

@login_required
def vista_operador(request):
    from .utils import get_operator_view_context
    
    # Verificar que el usuario es un operador
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or (perfil.rol or '').strip().lower() != 'operador':
        return redirect('login')
    
    # Obtener contexto para la vista de operador usando el User actual
    context = get_operator_view_context(request.user, request)
    
    return render(request, 'licitaciones/gestion_licitaciones_operador.html', context)

@login_required
def vista_operador_manual(request):
    from .utils import get_operator_view_context
    
    # Verificar si hay un operador seleccionado manualmente
    operador_user_id = request.session.get('operador_manual_id')
    if not operador_user_id:
        return redirect('login')
    
    # Obtener el User
    from django.contrib.auth.models import User
    operador_user = User.objects.filter(id=operador_user_id).first()
    
    # Obtener contexto para la vista de operador
    context = get_operator_view_context(operador_user, request)
    context['es_operador_manual'] = True
    context['es_operador'] = False
    
    return render(request, 'licitaciones/gestion_licitaciones_operador.html', context)

@login_required
def licitaciones_operador(request):
    from .utils import get_operator_view_context
    
    # Verificar que el usuario es un operador
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or (perfil.rol or '').strip().lower() != 'operador':
        return redirect('login')
    
    # Obtener contexto para la vista de operador ordenando por fecha de creación
    context = get_operator_view_context(request.user, request, sort_by='-fecha_creacion')
    
    return render(request, 'licitaciones/gestion_licitaciones_operador.html', context)

@login_required
def vista_vizualizador(request):
    # Verificar que el usuario es un administrador
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or (perfil.rol or '').strip().lower() != 'vizualizador':
        return redirect('login')
    # Obtener todas las licitaciones ordenadas por ID descendente
    proyectos_list = Licitacion.objects.select_related(
        'operador_user', 'operador_2', 'etapa_fk', 'estado_fk', 'tipo_licitacion',
        'moneda', 'categoria', 'departamento', 'licitacion_fallida_linkeada'
    ).prefetch_related('financiamiento').order_by('-id')

    # Aplicar filtros comunes (fallidas, anuales, búsqueda)
    proyectos_list = get_filtered_projects_list(proyectos_list, request)
    
    # Paginar resultados
    proyectos = get_paginated_projects(proyectos_list, request)
    
    # Obtener todos los catálogos de datos
    catalogs = get_catalog_data()
    
    # Construir el contexto para la plantilla

    context = {
        'proyectos': proyectos,
        'paginator': proyectos.paginator,
        'operadores': User.objects.filter(perfil__rol__in=['operador', 'admin']),
        'es_vizualizador': True,
        **catalogs  # Incluir todos los catálogos
    }
    return render(request, 'licitaciones/gestion_licitaciones_visita.html', context)

@login_required
def licitaciones_vizualizador(request):
    # Verificar que el usuario es un administrador
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or (perfil.rol or '').strip().lower() != 'admin':
        return redirect('login')
    # Obtener todas las licitaciones ordenadas por ID descendente
    proyectos_list = Licitacion.objects.select_related(
        'operador_user', 'operador_2', 'etapa_fk', 'estado_fk', 'tipo_licitacion',
        'moneda', 'categoria', 'departamento', 'licitacion_fallida_linkeada'
    ).prefetch_related('financiamiento').order_by('-id')

    # Aplicar filtros comunes (fallidas, anuales, búsqueda)
    proyectos_list = get_filtered_projects_list(proyectos_list, request)
    
    # Paginar resultados
    proyectos = get_paginated_projects(proyectos_list, request)
    
    # Obtener todos los catálogos de datos
    catalogs = get_catalog_data()
    
    # Construir el contexto para la plantilla
    context = {
        'proyectos': proyectos,
        'paginator': proyectos.paginator,
        'operadores': User.objects.filter(perfil__rol__in=['operador', 'admin']),
        'es_vizualizador': True,
        **catalogs  # Incluir todos los catálogos
    }
    
    return render(request, 'licitaciones/gestion_licitaciones_visita.html', context)

@csrf_exempt
def login_view(request):
    from .models import Perfil
    import logging
    
    if request.method == 'POST':
        login_type = request.POST.get('login_type', 'admin')
        
        if login_type == 'operador':
            # Login de operador como User con perfil operador
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            # Intentar autenticar al usuario
            user = authenticate(request, username=username, password=password)
            
            if user and user.is_authenticated:
                perfil = getattr(user, 'perfil', None)
                # Verificar si el usuario es operador manual
                if perfil and perfil.rol == 'admin':
                    login(request, user)
                    request.session['operador_manual_id'] = user.id
                    return redirect('vista_operador_manual')
                elif perfil and perfil.rol == 'operador':
                    login(request, user)
                    return redirect('vista_operador')
                elif perfil and perfil.rol == 'vizualizador':
                    login(request, user)
                    return redirect('vista_vizualizador')
                else:
                    error_msg = 'Usuario no tiene permisos de operador.'
                    return render(request, 'licitaciones/login.html', {
                        'error': error_msg,
                        'login_type': 'operador'
                    })
            else:
                error_msg = 'Credenciales de operador incorrectas.'
                return render(request, 'licitaciones/login.html', {
                    'error': error_msg,
                    'login_type': 'operador'
                })
        
        else:
            # Login de administrador (Django estándar)
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                try:
                    perfil = user.perfil
                    rol = (perfil.rol or '').strip().lower()
                    if rol == 'admin':
                        return redirect('vista_admin')
                    elif rol == 'operador':
                        return redirect('vista_operador')
                    elif rol == 'vizualizador':
                        return redirect('vista_vizualizador')
                    else:
                        logout(request)
                        return render(request, 'licitaciones/login.html', {
                            'form': form, 
                            'error': f'Rol no válido: {perfil.rol}',
                            'login_type': 'admin'
                        })
                except Perfil.DoesNotExist:
                    logout(request)
                    return render(request, 'licitaciones/login.html', {
                        'form': form, 
                        'error': 'Usuario sin perfil asignado',
                        'login_type': 'admin'
                    })
                except Exception as e:
                    logging.exception('Error en login_view')
                    logout(request)
                    return render(request, 'licitaciones/login.html', {
                        'form': form, 
                        'error': 'Error inesperado en el login. Contacte al administrador.',
                        'login_type': 'admin'
                    })
            else:
                return render(request, 'licitaciones/login.html', {
                    'form': form, 
                    'error': 'Credenciales de administrador incorrectas',
                    'login_type': 'admin'
                })
    
    else:
        form = AuthenticationForm()
    
    return render(request, 'licitaciones/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

#ESTADISTICTICAS
@login_required
def estadisticas_view(request):
    # Verificar que sea admin
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.rol != 'admin':
        return HttpResponseForbidden("Acceso denegado")
    
    total_licitaciones = Licitacion.objects.count()
    # Contar usuarios con perfil de operador
    total_operadores = User.objects.filter(perfil__rol='operador').count()
    # Licitaciones por operador ahora usando User
    licitaciones_por_operador = (
        User.objects.filter(perfil__rol='operador')
        .annotate(num_licitaciones=Count('licitaciones_asignadas'))
        .annotate(nombre=F('username'))  # Para compatibilidad con template
    )
    licitaciones_por_etapa = (
        Etapa.objects.annotate(num_licitaciones=Count('proyectos_etapa'))
    )
    hace_30_dias = timezone.now() - timezone.timedelta(days=30)
    licitaciones_ultimo_mes = Licitacion.objects.filter(fecha_creacion__gte=hace_30_dias).count()
    
    return render(request, 'licitaciones/estadisticas.html', {
        'total_licitaciones': total_licitaciones,
        'total_operadores': total_operadores,
        'licitaciones_por_operador': licitaciones_por_operador,
        'licitaciones_por_etapa': licitaciones_por_etapa,
        'licitaciones_ultimo_mes': licitaciones_ultimo_mes,
        'es_admin': True,
        'es_operador': False,
        'es_operador_manual': False,
        'operador_sidebar_nombre': None,
    })

def logout_operador_manual(request):
    if 'operador_manual_id' in request.session:
        del request.session['operador_manual_id']
    return redirect('login')

def es_usuario_operador(user):
    """
    Función auxiliar para verificar si un usuario es operador
    """
    if not user or not user.is_authenticated:
        return False
    
    # Verificar si tiene perfil de operador
    try:
        if hasattr(user, 'perfil') and user.perfil.rol == 'operador':
            return True
    except AttributeError:
        pass
    
    # Verificar si está asignado como operador en alguna licitación
    from .models import Licitacion
    if Licitacion.objects.filter(operador_user=user).exists() or Licitacion.objects.filter(operador_2=user).exists():
        return True
    
    return False

def bitacora_licitacion(request, licitacion_id):
    # Permitir acceso a admin y operadores (solo lectura para operadores)
    user_rol = None
    es_admin = False
    es_operador = False
    es_vizualizador = False
    es_operador_manual = False
    operador_sidebar_nombre = None
    
    # Verificar si el usuario está autenticado
    if not request.user.is_authenticated:
        return HttpResponseForbidden('Debe iniciar sesión para acceder a la bitácora.')
    
    # Verificar si viene desde la vista de operador
    from_operador = request.GET.get('from') == 'operador'
    
    # Método 1: Verificar perfil del usuario
    try:
        if hasattr(request.user, 'perfil') and request.user.perfil:
            rol = getattr(request.user.perfil, 'rol', '').strip().lower()
            if rol == 'admin':
                es_admin = True
                user_rol = 'admin'
            elif rol == 'vizualizador':
                user_rol = 'vizualizador'
                es_vizualizador = True
            elif rol == 'operador':
                es_operador = True
                user_rol = 'operador'
                operador_sidebar_nombre = request.user.get_full_name() or request.user.username
    except (AttributeError, Exception):
        pass
    
    # Método 2: Verificar si es operador por función auxiliar
    if not (es_admin or es_operador or es_vizualizador) and es_usuario_operador(request.user):
        es_operador = True
        user_rol = 'operador'
        operador_sidebar_nombre = request.user.get_full_name() or request.user.username
    
    # Método 3: Verificar sessions de respaldo
    if not (es_admin or es_operador or es_vizualizador):
        if 'operador_id' in request.session:
            es_operador = True
            user_rol = 'operador'
            # Legacy session handling - get user by ID
            operador_user = User.objects.filter(id=request.session['operador_id']).first()
            if operador_user:
                operador_sidebar_nombre = operador_user.get_full_name() or operador_user.username
        elif 'operador_manual_id' in request.session:
            es_operador_manual = True
            user_rol = 'operador_manual'
            # Manual operador session handling - get user by ID
            operador_user = User.objects.filter(id=request.session['operador_manual_id']).first()
            if operador_user:
                operador_sidebar_nombre = operador_user.get_full_name() or operador_user.username
    
    # Método 4: Si viene de vista de operador y está autenticado, permitir acceso
    if not (es_admin or es_operador or es_operador_manual or es_vizualizador) and from_operador:
        es_operador = True
        user_rol = 'operador'
        operador_sidebar_nombre = request.user.get_full_name() or request.user.username
    
    # Si no es admin ni operador, denegar acceso
    if not (es_admin or es_operador or es_operador_manual or es_vizualizador):
        return HttpResponseForbidden('Solo administradores u operadores pueden acceder a la bitácora.')
    
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    bitacora_qs = BitacoraLicitacion.objects.filter(licitacion=licitacion).order_by('-fecha')
    from django.core.paginator import Paginator
    page_number = request.GET.get('page')
    paginator = Paginator(bitacora_qs, 10)
    bitacoras = paginator.get_page(page_number)
    
    if request.method == 'POST':
        tipo_accion = request.POST.get('tipo_accion')

        # ==========================================================
        #  NUEVA LÓGICA: INSERTAR ETAPA USANDO 'TipoLicitacionEtapa'
        # ==========================================================
        if tipo_accion == 'crear_etapa_en_flujo':
            nombre_nueva_etapa = request.POST.get('nombre_nueva_etapa')
            id_tipo_seleccionado = request.POST.get('tipo_licitacion_select') # El tipo elegido en el modal
            id_etapa_referencia = request.POST.get('etapa_referencia_select') # La etapa "después de la cual" va la nueva
            tipo_lic_obj = get_object_or_404(TipoLicitacion, id=id_tipo_seleccionado)
            print(f"Insertando en Tipo: {tipo_lic_obj.nombre}")
            orden_referencia = 0
            # 2. Buscar el ORDEN de la etapa actual
            if id_etapa_referencia:
                try:
                    relacion_ref = TipoLicitacionEtapa.objects.get(
                        tipo_licitacion=tipo_lic_obj,
                        etapa_id=id_etapa_referencia
                    )
                    orden_referencia = relacion_ref.orden
                    print(f"Referencia seleccionada: {relacion_ref.etapa.nombre} (Orden {orden_referencia})")
                except TipoLicitacionEtapa.DoesNotExist:
                    # Si eligió "Al inicio" o falló algo, asumimos orden 0
                    orden_referencia = 0
            
            # 3. HACER ESPACIO (Empujamos las etapas siguientes)
            TipoLicitacionEtapa.objects.filter(
                tipo_licitacion=tipo_lic_obj,
                orden__gt=orden_referencia
            ).update(orden=F('orden') + 1)

            # 4. CREAR O OBTENER LA ETAPA
            nueva_etapa_obj, _ = Etapa.objects.get_or_create(nombre=nombre_nueva_etapa)

            # 5. INSERTAR LA RELACIÓN
            TipoLicitacionEtapa.objects.create(
                tipo_licitacion=tipo_lic_obj,
                etapa=nueva_etapa_obj,
                orden=orden_referencia + 1
            )
            
            messages.success(request, f"Etapa '{nombre_nueva_etapa}' insertada en '{tipo_lic_obj.nombre}' orden {orden_referencia + 1}.")
            return redirect('bitacora_licitacion', licitacion_id=licitacion_id)
        
        
        if (es_operador or es_operador_manual) and not licitacion.puede_operar_usuario(request.user):
            return JsonResponse({
                'ok': False, 
                'error': f'Solo el operador activo puede agregar entradas. Operador activo actual: {licitacion.get_operador_activo()}'
            }, status=403)
        valores = {}
        texto = request.POST.get('texto', '').strip()
        archivo = request.FILES.get('archivo')
        etapa_id = request.POST.get('etapa')
        etapa_nombre = request.POST.get('etapa_nombre')
        etapa_obj = None
        if etapa_id:
            try:
                etapa_obj = Etapa.objects.get(id=etapa_id)
            except Etapa.DoesNotExist:
                etapa_obj = None
        if etapa_nombre:
            if 'evaluación de ofertas' in etapa_nombre.strip().lower() and 'trato directo' in licitacion.tipo_licitacion.nombre.strip().lower():
                etapa_nombre = 'Evaluación de la cotización'
            try:
                etapa_obj = Etapa.objects.get(nombre = etapa_nombre)
            except Etapa.DoesNotExist:
                etapa_obj = None
        

        id_mercado_publico = request.POST.get('id_mercado_publico', '').strip()
        
        operador_2_id = request.POST.get('operador_2')
        
        if operador_2_id:
            try:
                nuevo_op2 = User.objects.get(id=operador_2_id)
                # Si es diferente al que ya tenía, lo actualizamos y guardamos en bitácora
                if licitacion.operador_2 != nuevo_op2:
                    valores['Asignación Operador 2'] = f"{nuevo_op2.first_name} {nuevo_op2.last_name}"
                    licitacion.operador_2 = nuevo_op2
                    licitacion.save()
            except User.DoesNotExist:
                pass
        # Campos específicos
        fecha_solicitud_intencion_compra = request.POST.get('fecha_solicitud_intencion_compra', '').strip()

        nombre_integrante_uno_comision_base = request.POST.get('nombre_integrante_uno_comision_base', '').strip()
        nombre_integrante_dos_comision_base = request.POST.get('nombre_integrante_dos_comision_base', '').strip()
        nombre_integrante_tres_comision_base = request.POST.get('nombre_integrante_tres_comision_base', '').strip()

        fecha_evaluacion_cotizacion = request.POST.get('fecha_evaluacion_cotizacion', '').strip()
        monto_estimado_cotizacion = request.POST.get('monto_estimado_cotizacion', '').strip()

        empresa_adjudicacion = request.POST.get('empresa_adjudicacion', '').strip()
        rut_adjudicacion = request.POST.get('rut_adjudicacion', '').strip()
        monto_adjudicacion = request.POST.get('monto_adjudicacion', '').strip()
        fecha_decreto_adjudicacion = request.POST.get('fecha_decreto_adjudicacion', '').strip()
        fecha_subida_mercado_publico_adjudicacion = request.POST.get('fecha_subida_mercado_publico_adjudicacion', '').strip()
        orden_compra_adjudicacion = request.POST.get('orden_compra_adjudicacion', '').strip()

        fecha_evaluacion_tecnica_evaluacion = request.POST.get('fecha_evaluacion_tecnica_evaluacion', '').strip()
        nombre_integrante_uno_evaluacion = request.POST.get('nombre_integrante_uno_evaluacion', '').strip()
        nombre_integrante_dos_evaluacion =request.POST.get('nombre_integrante_dos_evaluacion', '').strip()
        nombre_integrante_tres_evaluacion = request.POST.get('nombre_integrante_tres_evaluacion', '').strip()
        fecha_comision_evaluacion = request.POST.get('fecha_comision_evaluacion', '').strip()

        fecha_cierre_preguntas_publicacionportal = request.POST.get('fecha_cierre_preguntas_publicacionportal', '').strip()
        fecha_respuesta_publicacionportal = request.POST.get('fecha_respuesta_publicacionportal', '').strip()
        fecha_visita_terreno_publicacionportal = request.POST.get('fecha_visita_terreno_publicacionportal', '').strip()
        fecha_cierre_oferta_publicacionportal = request.POST.get('fecha_cierre_oferta_publicacionportal', '').strip()
        fecha_apertura_tecnica_publicacionportal = request.POST.get('fecha_apertura_tecnica_publicacionportal', '').strip()
        fecha_apertura_economica_publicacionportal = request.POST.get('fecha_apertura_economica_publicacionportal', '').strip()
        fecha_estimada_adjudicacion_publicacionportal = request.POST.get('fecha_estimada_adjudicacion_publicacionportal', '').strip()

        fecha_disponibilidad_presupuestaria = request.POST.get('fecha_disponibilidad_presupuestaria', '').strip()

        fecha_publicacion_mercado_publico = request.POST.get('fecha_publicacion_mercado_publico', '').strip()
        fecha_cierre_ofertas_mercado_publico = request.POST.get('fecha_cierre_ofertas_mercado_publico', '').strip()

        fecha_solicitud_regimen_interno = request.POST.get('fecha_solicitud_regimen_interno', '').strip()

        fecha_recepcion_documento_regimen_interno = request.POST.get('fecha_recepcion_documento_regimen_interno', '').strip()

        
        fecha_tope_firma_contrato = request.POST.get('fecha_tope_firma_contrato', '').strip()
        accion_etapa = request.POST.get('accion_etapa')
        es_redestinacion = request.POST.get('redestinar', '') == 'true'


        # --- 1. Lógica de Limpieza (Solo si es Redestinar) ---
        if es_redestinacion and etapa_obj:
            valores['Redestinado'] = str(etapa_nombre)
            # Limpiar datos futuros para reiniciar el proceso
            if licitacion.tipo_licitacion and 'trato directo' in licitacion.tipo_licitacion.nombre.lower().strip():
                licitacion.fecha_disponibilidad_presupuestaria = None
            licitacion.fecha_evaluacion_cotizacion = None
            licitacion.monto_estimado_cotizacion = None
            licitacion.empresa_adjudicacion = None
            licitacion.rut_adjudicacion = None
            licitacion.monto_adjudicacion = None
            licitacion.fecha_decreto_adjudicacion = None
            licitacion.fecha_subida_mercado_publico_adjudicacion = None
            licitacion.orden_compra_adjudicacion = None
            licitacion.fecha_evaluacion_tecnica_evaluacion = None
            licitacion.nombre_integrante_uno_evaluacion = None
            licitacion.nombre_integrante_dos_evaluacion = None
            licitacion.nombre_integrante_tres_evaluacion = None
            licitacion.fecha_comision_evaluacion = None
            licitacion.fecha_solicitud_regimen_interno = None
            licitacion.fecha_recepcion_documento_regimen_interno = None
            licitacion.fecha_tope_firma_contrato = None
            fecha_tope_firma_contrato = None
            licitacion.save()

        # --- 2. Lógica de "El Puntero" (¿Se mueve la etapa actual?) ---
        if etapa_obj:
            debe_cambiar_etapa = False # Por seguridad, empezamos en NO

            # A. Si es Redestinación -> SIEMPRE CAMBIA (Retrocede/Reinicia)
            if es_redestinacion:
                debe_cambiar_etapa = True
            
            # B. Si no tiene etapa actual -> SIEMPRE CAMBIA (Inicializa)
            elif not licitacion.etapa_fk:
                debe_cambiar_etapa = True

            # C. Caso Normal: Comparar órdenes matemáticamente
            else:
                try:
                    rel_actual = TipoLicitacionEtapa.objects.filter(
                        tipo_licitacion=licitacion.tipo_licitacion, 
                        etapa=licitacion.etapa_fk
                    ).first()
                    
                    rel_nueva = TipoLicitacionEtapa.objects.filter(
                        tipo_licitacion=licitacion.tipo_licitacion, 
                        etapa=etapa_obj
                    ).first()

                    if rel_actual and rel_nueva:
                        # Si la NUEVA es MAYOR que la ACTUAL -> AVANZA
                        if rel_nueva.orden > rel_actual.orden:
                            debe_cambiar_etapa = True
                        
                        # Si la NUEVA es MENOR o IGUAL -> NO HACE NADA (Se queda en la avanzada)
                        else:
                            debe_cambiar_etapa = False
                    else:
                        # Si no hay configuración de orden, mejor no mover por seguridad
                        debe_cambiar_etapa = False
                        
                except Exception as e:
                    print(f"Error calculando orden: {e}")
                    debe_cambiar_etapa = False

            # --- Ejecutar cambio si corresponde ---
            if debe_cambiar_etapa:
                licitacion.etapa_fk = etapa_obj
                licitacion.save()
        # Actualizar información adicional para ciertas etapas
        if id_mercado_publico:
            licitacion.id_mercado_publico = id_mercado_publico
        
        
        
        if etapa_obj and 'decreto de intención de compra' in etapa_obj.nombre.lower().strip():
            if fecha_solicitud_intencion_compra and licitacion.fecha_solicitud_intencion_compra != datetime.strptime(fecha_solicitud_intencion_compra, '%Y-%m-%d').date():
                valores['Fecha de la evaluación de cotización'] = datetime.strptime(fecha_solicitud_intencion_compra, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_solicitud_intencion_compra = fecha_solicitud_intencion_compra
        
        if etapa_obj and 'comisión de base' in etapa_obj.nombre.lower().strip():
            if nombre_integrante_uno_comision_base and licitacion.nombre_integrante_uno_comision_base != nombre_integrante_uno_comision_base:
                valores['Nombre integrante uno comisión de base'] = str(nombre_integrante_uno_comision_base)
                licitacion.nombre_integrante_uno_comision_base = nombre_integrante_uno_comision_base
            if nombre_integrante_dos_comision_base and licitacion.nombre_integrante_dos_comision_base != nombre_integrante_dos_comision_base:
                valores['Nombre integrante dos comisión de base'] = str(nombre_integrante_dos_comision_base)
                licitacion.nombre_integrante_dos_comision_base = nombre_integrante_dos_comision_base
            if nombre_integrante_tres_comision_base and licitacion.nombre_integrante_tres_comision_base != nombre_integrante_tres_comision_base:
                valores['Nombre integrante tres comisión de base'] = str(nombre_integrante_tres_comision_base)
                licitacion.nombre_integrante_tres_comision_base = nombre_integrante_tres_comision_base

        if etapa_obj and 'evaluación de la cotización' in etapa_obj.nombre.lower().strip():
            if fecha_evaluacion_cotizacion and licitacion.fecha_evaluacion_cotizacion != datetime.strptime(fecha_evaluacion_cotizacion, '%Y-%m-%d').date():
                valores['Fecha de la evaluación de cotización'] = datetime.strptime(fecha_evaluacion_cotizacion, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_evaluacion_cotizacion = fecha_evaluacion_cotizacion
            if monto_estimado_cotizacion and licitacion.monto_estimado_cotizacion != monto_estimado_cotizacion:
                valores['Monto estimado de la cotización'] = str(monto_estimado_cotizacion)
                licitacion.monto_estimado_cotizacion = monto_estimado_cotizacion

        if etapa_obj and 'adjudicación' in etapa_obj.nombre.lower().strip():
            if empresa_adjudicacion and licitacion.empresa_adjudicacion != empresa_adjudicacion:
                valores['Empresa adjudicada'] = str(empresa_adjudicacion)
                licitacion.empresa_adjudicacion = empresa_adjudicacion
            if rut_adjudicacion and licitacion.rut_adjudicacion != rut_adjudicacion:
                valores['Rut de la empresa adjudicada'] = str(rut_adjudicacion)
                licitacion.rut_adjudicacion = rut_adjudicacion
            if monto_adjudicacion and licitacion.monto_adjudicacion != monto_adjudicacion:
                valores['Monto adjudicado'] = str(monto_adjudicacion)
                try:
                    licitacion.monto_adjudicacion = float(monto_adjudicacion)
                except ValueError:
                    pass
            if fecha_decreto_adjudicacion and licitacion.fecha_decreto_adjudicacion != datetime.strptime(fecha_decreto_adjudicacion, '%Y-%m-%d').date():
                valores['Fecha de decreto de adjudicación'] = datetime.strptime(fecha_decreto_adjudicacion, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_decreto_adjudicacion = fecha_decreto_adjudicacion
            if fecha_subida_mercado_publico_adjudicacion and licitacion.fecha_subida_mercado_publico_adjudicacion != datetime.strptime(fecha_subida_mercado_publico_adjudicacion, '%Y-%m-%d').date():
                valores['Fecha de subida a Mercado Público'] = datetime.strptime(fecha_subida_mercado_publico_adjudicacion, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_subida_mercado_publico_adjudicacion = fecha_subida_mercado_publico_adjudicacion
            if orden_compra_adjudicacion and licitacion.orden_compra_adjudicacion != orden_compra_adjudicacion:
                valores['Orden de compra'] = str(orden_compra_adjudicacion)
                licitacion.orden_compra_adjudicacion = orden_compra_adjudicacion
        if etapa_obj and 'evaluación de ofertas' in etapa_obj.nombre.lower().strip():
            if fecha_evaluacion_tecnica_evaluacion and licitacion.fecha_evaluacion_tecnica_evaluacion != datetime.strptime(fecha_evaluacion_tecnica_evaluacion, '%Y-%m-%d').date():
                valores['Fecha de evaluación técnica'] = datetime.strptime(fecha_evaluacion_tecnica_evaluacion, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_evaluacion_tecnica_evaluacion = fecha_evaluacion_tecnica_evaluacion
            if nombre_integrante_uno_evaluacion and licitacion.nombre_integrante_uno_evaluacion != nombre_integrante_uno_evaluacion:
                valores['Nombre integrante uno comisión evaluadora'] = str(nombre_integrante_uno_evaluacion)
                licitacion.nombre_integrante_uno_evaluacion = nombre_integrante_uno_evaluacion
            if nombre_integrante_dos_evaluacion and licitacion.nombre_integrante_dos_evaluacion != nombre_integrante_dos_evaluacion:
                valores['Nombre integrante dos comisión evaluadora'] = str(nombre_integrante_dos_evaluacion)
                licitacion.nombre_integrante_dos_evaluacion = nombre_integrante_dos_evaluacion
            if nombre_integrante_tres_evaluacion and licitacion.nombre_integrante_tres_evaluacion != nombre_integrante_tres_evaluacion:
                valores['Nombre integrante tres comisión evaluadora'] = str(nombre_integrante_tres_evaluacion)
                licitacion.nombre_integrante_tres_evaluacion = nombre_integrante_tres_evaluacion
            if fecha_comision_evaluacion and licitacion.fecha_comision_evaluacion != datetime.strptime(fecha_comision_evaluacion, '%Y-%m-%d').date():
                valores['Fecha de comisión evaluación'] = datetime.strptime(fecha_comision_evaluacion, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_comision_evaluacion = fecha_comision_evaluacion
        if etapa_obj and 'publicación en portal' in etapa_obj.nombre.lower().strip():
            if fecha_cierre_preguntas_publicacionportal and licitacion.fecha_cierre_preguntas_publicacionportal != datetime.strptime(fecha_cierre_preguntas_publicacionportal, '%Y-%m-%d').date():
                valores['Fecha de cierre de preguntas'] = datetime.strptime(fecha_cierre_preguntas_publicacionportal, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_cierre_preguntas_publicacionportal = fecha_cierre_preguntas_publicacionportal
            if fecha_respuesta_publicacionportal and licitacion.fecha_respuesta_publicacionportal != datetime.strptime(fecha_respuesta_publicacionportal, '%Y-%m-%d').date():
                valores['Fecha de respuesta'] = datetime.strptime(fecha_respuesta_publicacionportal, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_respuesta_publicacionportal = fecha_respuesta_publicacionportal
            if fecha_visita_terreno_publicacionportal and licitacion.fecha_visita_terreno_publicacionportal != datetime.strptime(fecha_visita_terreno_publicacionportal, '%Y-%m-%d').date():
                valores['Fecha de visita a terreno'] = datetime.strptime(fecha_visita_terreno_publicacionportal, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_visita_terreno_publicacionportal = fecha_visita_terreno_publicacionportal
            if fecha_cierre_oferta_publicacionportal and licitacion.fecha_cierre_oferta_publicacionportal != datetime.strptime(fecha_cierre_oferta_publicacionportal, '%Y-%m-%d').date():
                valores['Fecha de cierre de oferta'] = datetime.strptime(fecha_cierre_oferta_publicacionportal, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_cierre_oferta_publicacionportal = fecha_cierre_oferta_publicacionportal
            if fecha_apertura_tecnica_publicacionportal and licitacion.fecha_apertura_tecnica_publicacionportal != datetime.strptime(fecha_apertura_tecnica_publicacionportal, '%Y-%m-%d').date():
                valores['Fecha de apertura técnica'] = datetime.strptime(fecha_apertura_tecnica_publicacionportal, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_apertura_tecnica_publicacionportal = fecha_apertura_tecnica_publicacionportal
            if fecha_apertura_economica_publicacionportal and licitacion.fecha_apertura_economica_publicacionportal != datetime.strptime(fecha_apertura_economica_publicacionportal, '%Y-%m-%d').date():
                valores['Fecha de apertura económica'] = datetime.strptime(fecha_apertura_economica_publicacionportal, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_apertura_economica_publicacionportal = fecha_apertura_economica_publicacionportal
            if fecha_estimada_adjudicacion_publicacionportal and licitacion.fecha_estimada_adjudicacion_publicacionportal != datetime.strptime(fecha_estimada_adjudicacion_publicacionportal, '%Y-%m-%d').date():
                valores['Fecha estimada de adjudicación'] = datetime.strptime(fecha_estimada_adjudicacion_publicacionportal, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_estimada_adjudicacion_publicacionportal = fecha_estimada_adjudicacion_publicacionportal

        
        if fecha_disponibilidad_presupuestaria and licitacion.fecha_disponibilidad_presupuestaria != datetime.strptime(fecha_disponibilidad_presupuestaria, '%Y-%m-%d').date() and etapa_obj and 'disponibilidad presupuestaria' in etapa_obj.nombre.lower().strip():
            valores['Fecha de disponibilidad presupuestaria'] = datetime.strptime(fecha_disponibilidad_presupuestaria, '%Y-%m-%d').strftime('%d-%m-%Y')
            licitacion.fecha_disponibilidad_presupuestaria = fecha_disponibilidad_presupuestaria
        
        if etapa_obj and 'publicación mercado público' in etapa_obj.nombre.lower().strip():
            if fecha_publicacion_mercado_publico and licitacion.fecha_publicacion_mercado_publico != datetime.strptime(fecha_publicacion_mercado_publico, '%Y-%m-%d').date():
                valores['Fecha de publicación en mercado público'] = datetime.strptime(fecha_publicacion_mercado_publico, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_publicacion_mercado_publico = fecha_publicacion_mercado_publico
            if fecha_cierre_ofertas_mercado_publico and licitacion.fecha_cierre_ofertas_mercado_publico != datetime.strptime(fecha_cierre_ofertas_mercado_publico, '%Y-%m-%d').date():
                valores['Fecha de cierre de ofertas en mercado público'] = datetime.strptime(fecha_cierre_ofertas_mercado_publico, '%Y-%m-%d').strftime('%d-%m-%Y')
                licitacion.fecha_cierre_ofertas_mercado_publico = fecha_cierre_ofertas_mercado_publico

        if fecha_solicitud_regimen_interno and licitacion.fecha_solicitud_regimen_interno != datetime.strptime(fecha_solicitud_regimen_interno, '%Y-%m-%d').date() and etapa_obj and ('solicitud de comisión de régimen interno' in etapa_obj.nombre.lower().strip() or 'solicitud de régimen interno' in etapa_obj.nombre.lower().strip()):
            valores['Fecha de solicitud de régimen interno'] = datetime.strptime(fecha_solicitud_regimen_interno, '%Y-%m-%d').strftime('%d-%m-%Y')
            licitacion.fecha_solicitud_regimen_interno = fecha_solicitud_regimen_interno
        if fecha_recepcion_documento_regimen_interno and licitacion.fecha_recepcion_documento_regimen_interno != datetime.strptime(fecha_recepcion_documento_regimen_interno, '%Y-%m-%d').date() and etapa_obj and 'recepción de documento de régimen interno' in etapa_obj.nombre.lower().strip():
            valores['Fecha de recepción de documento régimen interno'] = datetime.strptime(fecha_recepcion_documento_regimen_interno, '%Y-%m-%d').strftime('%d-%m-%Y')
            licitacion.fecha_recepcion_documento_regimen_interno = fecha_recepcion_documento_regimen_interno
        if fecha_tope_firma_contrato and licitacion.fecha_tope_firma_contrato != datetime.strptime(fecha_tope_firma_contrato, '%Y-%m-%d').date() and etapa_obj and 'firma de contrato' in etapa_obj.nombre.lower().strip():
            valores['Fecha tope de firma de contrato'] = datetime.strptime(fecha_tope_firma_contrato, '%Y-%m-%d').strftime('%d-%m-%Y')
            licitacion.fecha_tope_firma_contrato = fecha_tope_firma_contrato
        licitacion.save()
        # Construir el texto de la bitácora con los campos modificados
        if valores:
            texto += "\n"
            texto += "\nCampos modificados:" + ''.join([
                f"\n- {campo}: '{valores[campo]}'"
                for campo in valores])
        
        operador_user = None
        if es_admin:
            operador_user = request.user
        elif es_operador or es_operador_manual:
            operador_user = request.user
            
        if texto or archivo:
            # Agregar información específica de etapa al texto
            texto_completo = texto
            
            bitacora = BitacoraLicitacion.objects.create(
                licitacion=licitacion,
                operador_user=operador_user,
                texto=texto_completo,
                etapa=etapa_obj
            )
            
            # Manejar archivos múltiples
            archivos = request.FILES.getlist('archivos')
            if archivos:
                from .models import DocumentoBitacora
                for archivo in archivos:
                    DocumentoBitacora.objects.create(
                        bitacora=bitacora,
                        archivo=archivo,
                        nombre=archivo.name
                    )
            
            # Manejar marcado como fallida
            marcar_fallida = request.POST.get('marcar_fallida') == 'on'
            if marcar_fallida:
                tipo_fallida = request.POST.get('tipo_fallida')
                if tipo_fallida:
                    licitacion.tipo_fallida = tipo_fallida
                    licitacion.save()
            
            return redirect('bitacora_licitacion', licitacion_id=licitacion_id)
    tipo_licitacion = licitacion.tipo_licitacion
    if tipo_licitacion:
        etapas_ids = list(TipoLicitacionEtapa.objects.filter(tipo_licitacion=tipo_licitacion).order_by('orden').values_list('etapa_id', flat=True))
        etapas_qs = Etapa.objects.filter(id__in=etapas_ids).order_by(models.Case(*[models.When(id=pk, then=pos) for pos, pk in enumerate(etapas_ids)]))
        etapas = list(etapas_qs.values('id', 'nombre'))
    else:
        etapas = list(Etapa.objects.order_by('id').values('id', 'nombre'))
    for e_inicio, e_fin in licitacion.get_saltar_etapas():
        etapas = [etapa for etapa in etapas if etapa['id'] not in range(e_inicio, e_fin+1)]
    usuarios_disponibles = User.objects.filter(is_active=True).order_by('first_name')
    lista_etapas_disponibles = Etapa.objects.all().order_by('nombre')
    # 👇 AGREGAR ESTO AL FINAL: Obtener TODAS las etapas del sistema para el selector
    catalogo_etapas = Etapa.objects.all().order_by('nombre')
    todos_tipos = TipoLicitacion.objects.all()
    
    # Creamos un diccionario gigante con la estructura: { id_tipo: [lista_etapas] }
    diccionario_flujos = {}
    
    for tipo in todos_tipos:
        stages = TipoLicitacionEtapa.objects.filter(
            tipo_licitacion=tipo
        ).select_related('etapa').order_by('orden')
        
        lista_etapas = []
        for s in stages:
            lista_etapas.append({
                'id_etapa': s.etapa.id,
                'nombre_etapa': s.etapa.nombre,
                'orden': s.orden
            })
        diccionario_flujos[tipo.id] = lista_etapas

    # Convertimos a JSON para que Javascript lo entienda
    json_flujos = json.dumps(diccionario_flujos)
    
    # También pasamos la lista de tipos para el Select
    lista_tipos_licitacion = todos_tipos
    
    return render(request, 'licitaciones/bitacora_licitacion.html', {
        'licitacion': licitacion,
        'bitacoras': bitacoras,
        'etapas': etapas,
        'es_admin': es_admin,
        'es_operador_manual': es_operador_manual,
        'es_operador': es_operador,
        'es_vizualizador': es_vizualizador,
        'paginator': paginator,
        'operador_sidebar_nombre': operador_sidebar_nombre,
        'usuarios': usuarios_disponibles, # 👈 2. AGREGAR ESTA LÍNEA AL CONTEXTO
        'catalogo_etapas': catalogo_etapas,  # <--- AGREGAR AL CONTEXTO
        'lista_etapas_disponibles': lista_etapas_disponibles, # <--- IMPORTANTE: Agrega esto al context
        'json_flujos': json_flujos,               # <--- NUEVO
        'lista_tipos_licitacion': lista_tipos_licitacion, # <--- NUEVO
        'lista_etapas_disponibles': lista_etapas_disponibles,
    })

@require_POST
@login_required
def subir_documentos_licitacion(request, licitacion_id):
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    archivos = request.FILES.getlist('documentos')
    docs = []
    
    # Obtener nombres de documentos existentes para esta licitación
    nombres_existentes = set(
        DocumentoLicitacion.objects.filter(licitacion=licitacion).values_list('nombre', flat=True)
    )
    
    for archivo in archivos:
        # Verificar si ya existe un documento con este nombre
        nombre_archivo = archivo.name
        if nombre_archivo in nombres_existentes:
            # Evitar crear duplicados
            continue
            
        doc = DocumentoLicitacion.objects.create(
            licitacion=licitacion,
            archivo=archivo,
            nombre=nombre_archivo
        )
        nombres_existentes.add(nombre_archivo)
        docs.append({
            'id': doc.id,
            'nombre': doc.nombre,
            'url': doc.archivo.url,
            'fecha_subida': doc.fecha_subida.strftime('%d/%m/%Y %H:%M')
        })
    return JsonResponse({'ok': True, 'documentos': docs})

@require_GET
@csrf_exempt
def listar_documentos_licitacion(request, licitacion_id):
    # Permitir si usuario autenticado o si operador_manual_id en sesión
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    # Documentos directos
    docs_licitacion = [
        {
            'id': doc.id,
            'nombre': doc.nombre,
            'url': doc.archivo.url,
            'fecha_subida': timezone.localtime(doc.fecha_subida).strftime('%d/%m/%Y %H:%M'),
            'origen': 'licitacion',
        }
        for doc in licitacion.documentos.all().order_by('-fecha_subida')
    ]
    # Documentos de bitácora
    docs_bitacora = []
    for bitacora in licitacion.bitacoras.all():
        for doc in getattr(bitacora, 'archivos', []).all():
            docs_bitacora.append({
                'id': doc.id,
                'nombre': doc.nombre,
                'url': doc.archivo.url,
                'fecha_subida': timezone.localtime(doc.fecha_subida).strftime('%d/%m/%Y %H:%M'),
                'origen': 'bitacora',
                'bitacora_id': bitacora.id,
                'bitacora_texto': bitacora.texto,
                'bitacora_fecha': timezone.localtime(bitacora.fecha).strftime('%d/%m/%Y %H:%M'),
            })    # Unir ambos, pero eliminar duplicados basados en el nombre del archivo
    # Primero convertimos a un diccionario para eliminar duplicados por nombre
    docs_dict = {}
    
    # Agregar documentos de licitación primero (tienen prioridad)
    for doc in docs_licitacion:
        key = doc['nombre'].lower().strip()  # Clave normalizada
        docs_dict[key] = doc
    
    # Agregar documentos de bitácora solo si no existen ya
    for doc in docs_bitacora:
        key = doc['nombre'].lower().strip()  # Clave normalizada
        if key not in docs_dict:
            docs_dict[key] = doc
    
    # Convertir de vuelta a lista
    docs = list(docs_dict.values())
    
    # Ordenar por fecha_subida descendente
    docs.sort(key=lambda d: d['fecha_subida'], reverse=True)
    
    # Verificar si hay licitación fallida vinculada
    licitacion_fallida_data = None
    if hasattr(licitacion, 'licitacion_fallida_linkeada') and licitacion.licitacion_fallida_linkeada:
        fallida = licitacion.licitacion_fallida_linkeada
        # Obtener la última entrada de bitácora de la licitación fallida
        ultima_bitacora = BitacoraLicitacion.objects.filter(licitacion=fallida).order_by('-fecha').first()
        
        operador_name = '-'
        if fallida.operador_user:
            operador_name = fallida.operador_user.get_full_name() or fallida.operador_user.username
        
        licitacion_fallida_data = {
            'id': fallida.id,
            'numero_pedido': fallida.numero_pedido,
            'iniciativa': fallida.iniciativa,
            'operador': operador_name,
            'etapa': fallida.etapa_fk.nombre if fallida.etapa_fk else '-',
            'fecha_creacion': timezone.localtime(fallida.fecha_creacion).strftime('%d/%m/%Y %H:%M') if fallida.fecha_creacion else '-',
            'fecha_fallo': timezone.localtime(ultima_bitacora.fecha).strftime('%d/%m/%Y %H:%M') if ultima_bitacora else '-',
            'url_bitacora': f"/bitacora/{fallida.id}/?from_documents=1&licitacion_id={licitacion.id}"
        }
    
    return JsonResponse({
        'ok': True, 
        'documentos': docs,
        'licitacion_fallida': licitacion_fallida_data
    })

# API para obtener la etapa actual de un proyecto
@require_GET
def etapa_actual_api(request, licitacion_id):
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    return JsonResponse({
        'etapa_id': licitacion.etapa_fk.id if licitacion.etapa_fk else '',
        'etapa_nombre': licitacion.etapa_fk.nombre if licitacion.etapa_fk else ''
    })

def etapas_licitacion_api(request, licitacion_id):
    """
    API que devuelve las etapas de una licitación con información de inhabilitación
    """
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    
    # Obtener todas las etapas con información de inhabilitación
    etapas_con_info = licitacion.get_etapas_todas_con_inhabilitacion()
    
    etapas_data = []
    for etapa_info in etapas_con_info:
        rel = etapa_info['rel']
        etapa = etapa_info['etapa']
        etapas_data.append({
            'id': etapa.id,
            'nombre': etapa.nombre,
            'orden': rel.orden,
            'inhabilitada': etapa_info['inhabilitada']
        })
    
    return JsonResponse({
        'etapas': etapas_data,
        'debe_saltar_etapas': len(licitacion.get_saltar_etapas()) > 0,
        'moneda': licitacion.moneda.nombre if licitacion.moneda else None,
        'monto': float(licitacion.monto_presupuestado) if licitacion.monto_presupuestado else None
    })

@csrf_exempt
def eliminar_documento_licitacion(request, licitacion_id, doc_id):
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    doc = get_object_or_404(DocumentoLicitacion, id=doc_id, licitacion=licitacion)
    doc.archivo.delete(save=False)
    doc.delete()
    return JsonResponse({'ok': True})

@require_POST
@csrf_exempt
def guardar_observacion_operador(request, licitacion_id):
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    comentario = request.POST.get('comentario')
    if comentario is None:
        comentario = request.POST.get('texto', '').strip()
    else:
        comentario = comentario.strip()
    avanzar_etapa = request.POST.get('avanzar_etapa') == 'true' or request.POST.get('avanzar_etapa') == 'on'
    retroceder_etapa = request.POST.get('retroceder_etapa') == 'true' or request.POST.get('retroceder_etapa') == 'on'
    
    # Verificar acción de etapa por el campo accion_etapa (para el formulario de bitácora)
    accion_etapa = request.POST.get('accion_etapa', 'none')
    if accion_etapa == 'advance':
        avanzar_etapa = True
    elif accion_etapa == 'retreat':
        retroceder_etapa = True
    
    archivos = request.FILES.getlist('archivos')
    operador_user = None
    if hasattr(request.user, 'perfil') and getattr(request.user.perfil, 'rol', None) == 'operador':
        operador_user = request.user
    elif 'operador_manual_id' in request.session:
        operador_user = User.objects.filter(id=request.session['operador_manual_id']).first()
    # Cambiar estado a 'fallido' si se marcó la casilla correspondiente
    marcar_fallida_val = request.POST.get('marcar_fallida')
    marcar_fallida = marcar_fallida_val in ['true', 'on', '1']
    tipo_fallida = request.POST.get('tipo_fallida', '').strip()
    
    # Validar que si se marca como fallida, se seleccione un tipo
    if marcar_fallida and not tipo_fallida:
        return JsonResponse({'ok': False, 'error': 'Debe seleccionar un tipo de falla.'}, status=400)
    
    # Validar que el tipo de falla sea válido si se proporciona
    if tipo_fallida and tipo_fallida not in ['revocada', 'anulada', 'desierta']:
        return JsonResponse({'ok': False, 'error': 'Tipo de falla no válido'}, status=400)
    
    if marcar_fallida:
        estado_fallido = Estado.objects.filter(nombre__icontains='fallid').first()
        if estado_fallido and licitacion.estado_fk != estado_fallido:
            licitacion.estado_fk = estado_fallido
            # Actualizar el tipo de falla si se proporciona
            if tipo_fallida:
                licitacion.tipo_fallida = tipo_fallida
            licitacion.save()
    if not comentario and not archivos:
        return JsonResponse({'ok': False, 'error': 'Debe ingresar un comentario o adjuntar archivos.'}, status=400)
    
    # Preparar el texto de la bitácora
    texto_bitacora = comentario if comentario else 'Archivo adjunto'
    if marcar_fallida and tipo_fallida:
        texto_bitacora += f"\n\n⚠️ LICITACIÓN MARCADA COMO FALLIDA ({tipo_fallida.upper()})"
    
    # Crear una sola observación de bitácora
    b = BitacoraLicitacion.objects.create(
        licitacion=licitacion,
        operador_user=operador_user,
        texto=texto_bitacora,
        etapa=licitacion.etapa_fk
    )
    from .models import DocumentoBitacora
    for archivo in archivos:
        DocumentoBitacora.objects.create(
            bitacora=b,
            archivo=archivo,
            nombre=archivo.name
        )
    nueva_etapa = None
    # Usar las etapas habilitadas (excluyendo etapas saltadas si aplica)
    etapas_habilitadas = licitacion.get_etapas_habilitadas()
    etapas_tipo = [rel.etapa for rel in etapas_habilitadas]
    
    try:
        idx = [e.id for e in etapas_tipo].index(licitacion.etapa_fk.id)
        if avanzar_etapa and idx < len(etapas_tipo) - 1:
            nueva_etapa = etapas_tipo[idx + 1]
            licitacion.etapa_fk = nueva_etapa
            licitacion.save()
            BitacoraLicitacion.objects.create(
                licitacion=licitacion,
                operador_user=operador_user,
                texto=f"Avance automático de etapa: {nueva_etapa.nombre}",
                etapa=nueva_etapa
            )
        elif retroceder_etapa and idx > 0:
            # Verificar si puede retroceder (solo si su última observación no avanzó etapa)
            ultima_bitacora = BitacoraLicitacion.objects.filter(
                licitacion=licitacion, 
                operador_user=operador_user
            ).order_by('-fecha').first()
            
            puede_retroceder = True
            if ultima_bitacora:
                texto_lower = ultima_bitacora.texto.lower()
                if 'avance automático de etapa' in texto_lower or 'avanzar etapa' in texto_lower:
                    puede_retroceder = False
            
            if not puede_retroceder:
                return JsonResponse({'ok': False, 'error': 'No puede retroceder etapa porque su última observación avanzó etapa.'}, status=400)
            
            nueva_etapa = etapas_tipo[idx - 1]
            licitacion.etapa_fk = nueva_etapa
            licitacion.save()
            BitacoraLicitacion.objects.create(
                licitacion=licitacion,
                operador_user=operador_user,
                texto=f"Retroceso automático de etapa: {nueva_etapa.nombre}",
                etapa=nueva_etapa
            )
    except Exception:
        pass
    return JsonResponse({'ok': True, 'cambio_etapa': bool(nueva_etapa)})

@csrf_exempt
def cerrar_licitacion_operador(request, licitacion_id):
    """
    Vista para cerrar una licitación desde la vista de operador.
    Cambia el estado a "CERRADA" (ID 3) y registra en la bitácora.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    
    # Verificar autenticación
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    
    # Obtener la licitación
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    
    # Verificar que la licitación no esté ya cerrada
    estado_cerrada = Estado.objects.filter(id=3).first()  # Estado "CERRADA" con ID 3
    if not estado_cerrada:
        return JsonResponse({'ok': False, 'error': 'Estado CERRADA no encontrado en la base de datos'}, status=500)
    
    if licitacion.estado_fk and licitacion.estado_fk.id == 3:
        return JsonResponse({'ok': False, 'error': 'La licitación ya está cerrada'}, status=400)
    
    # Obtener los datos del formulario
    motivo_cierre = request.POST.get('texto', '').strip()
    licitacion_fallida = request.POST.get('licitacion_fallida') in ['true', 'on', '1']
    tipo_fallida = request.POST.get('tipo_fallida', '').strip()
    
    # Validar que se haya ingresado un motivo
    if not motivo_cierre:
        return JsonResponse({'ok': False, 'error': 'Debe especificar el motivo del cierre'}, status=400)
    
    # Validar que si está marcada como fallida, se haya seleccionado un tipo
    if licitacion_fallida and not tipo_fallida:
        return JsonResponse({'ok': False, 'error': 'Debe seleccionar el tipo de falla para una licitación fallida'}, status=400)
    
    # Validar que el tipo de falla sea válido si se proporciona
    if tipo_fallida and tipo_fallida not in ['revocada', 'anulada', 'desierta']:
        return JsonResponse({'ok': False, 'error': 'Tipo de falla no válido'}, status=400)
    
    # Obtener el operador
    operador_user = None
    if hasattr(request.user, 'perfil') and getattr(request.user.perfil, 'rol', None) == 'operador':
        operador_user = request.user
    elif 'operador_manual_id' in request.session:
        operador_user = User.objects.filter(id=request.session['operador_manual_id']).first()
    
    try:
        # Construir el texto para la bitácora
        texto_bitacora = f"🔒 LICITACIÓN CERRADA\n\nMotivo: {motivo_cierre}"
        
        if licitacion_fallida:
            texto_bitacora += f"\n\nEstado adicional:\n- Licitación fue FALLIDA ({tipo_fallida.upper()})"
            estado_cerrada = Estado.objects.filter(nombre__icontains='fallid').first()
        
        # Actualizar el campo tipo_fallida si es necesario
        if licitacion_fallida and tipo_fallida:
            licitacion.tipo_fallida = tipo_fallida
        
        # Cambiar el estado de la licitación a "CERRADA"
        licitacion.estado_fk = estado_cerrada
        licitacion.save()
        
        # Registrar en la bitácora
        BitacoraLicitacion.objects.create(
            licitacion=licitacion,
            operador_user=operador_user,
            texto=texto_bitacora,
            etapa=licitacion.etapa_fk
        )
        
        return JsonResponse({
            'ok': True, 
            'mensaje': 'Licitación cerrada correctamente',
            'nuevo_estado': estado_cerrada.nombre
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': f'Error al cerrar la licitación: {str(e)}'}, status=500)

@login_required
@require_http_methods(["GET", "POST", "DELETE"])
@csrf_exempt
def observacion_bitacora_api(request, bitacora_id):
    bitacora = get_object_or_404(BitacoraLicitacion, id=bitacora_id)

    # --- GET: devuelve texto (si existe)
    if request.method == 'GET':
        # Si es OneToOneField con related_name='observacion'
        obs = getattr(bitacora, 'observacion', None)
        if obs:
            return JsonResponse({'ok': True, 'texto': obs.texto})
        return JsonResponse({'ok': False, 'error': 'Sin observación'})

    # --- DELETE: borra observación (si existe)
    if request.method == 'DELETE':
        obs = getattr(bitacora, 'observacion', None)
        if obs:
            obs.delete()
            return JsonResponse({'ok': True})
        return JsonResponse({'ok': False, 'error': 'No existe observación'})

    # --- POST: crea/actualiza y adjunta archivos
    # Soporta application/json y multipart/form-data
    content_type = (request.META.get('CONTENT_TYPE') or '').lower()

    if 'application/json' in content_type:
        # Cuerpo JSON
        import json
        try:
            data = json.loads(request.body.decode('utf-8') or '{}')
        except Exception:
            return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)
        texto = (data.get('texto') or '').strip()
        archivos = []  # en JSON no vendrán archivos
    else:
        # FormData / x-www-form-urlencoded
        texto = (request.POST.get('texto') or '').strip()
        archivos = request.FILES.getlist('archivos')  # name="archivos" (sin [])

    if not texto:
        return JsonResponse({'ok': False, 'error': 'Texto vacío'}, status=400)

    # Obtiene o crea la observación ligada a la bitácora
    obs, _created = ObservacionBitacora.objects.get_or_create(bitacora=bitacora)
    obs.texto = texto
    obs.user = request.user
    obs.save()

    # Adjunta archivos (si vinieron)
    for archivo in archivos:
        DocumentoObservacion.objects.create(
            observacion=obs,
            archivo=archivo,
            nombre=archivo.name
        )

    return JsonResponse({'ok': True})
#agregarproyecto y aqui se guarda.
@csrf_exempt
def agregar_proyecto(request):
    try:
        data = json.loads(request.body)
        numero_pedido = data.get('numero_pedido')
        if not numero_pedido:
            return JsonResponse({'ok': False, 'error': 'El N° de pedido es obligatorio.'}, status=400)
        # if Licitacion.objects.filter(numero_pedido=numero_pedido).exists():
        #     return JsonResponse({'ok': False, 'error': 'No se puede guardar una licitación con un N° de pedido repetido.'}, status=400)        # Obtener el estado "En curso" (o el que corresponda)
        estado_en_curso = Estado.objects.filter(nombre__iexact='en curso').first()        # Convertir el monto a número de forma segura
        try:
            monto_presupuestado = float(data.get('monto_presupuestado') or 0)
        except (ValueError, TypeError):
            monto_presupuestado = 0
        #tipo_presupuesto = get_tipo_presupuesto(Moneda.objects.get(id=data.get('moneda')) if data.get('moneda') else None, monto_presupuestado)
        tipo_presupuesto = data.get('tipo_presupuesto')
        
        # Crear la licitación
        licitacion = Licitacion(
            numero_pedido=numero_pedido,
            id_mercado_publico=data.get('id_mercado_publico', ''),
            numero_cuenta=data.get('numero_cuenta', ''),
            operador_user=User.objects.get(id=data.get('operador')) if data.get('operador') else None,
            operador_2=User.objects.get(id=data.get('operador_2')) if data.get('operador_2') else None,
            tipo_licitacion=TipoLicitacion.objects.get(id=data.get('tipo_licitacion')) if data.get('tipo_licitacion') else None,
            moneda=Moneda.objects.get(id=data.get('moneda')) if data.get('moneda') else None,
            categoria=Categoria.objects.get(id=data.get('categoria')) if data.get('categoria') else None,
            en_plan_anual=data.get('en_plan_anual', False),
            justificacion_plan=data.get('justificacion_plan', ''), # ◄---- AGREGA ESTA LÍNEA
            iniciativa=data.get('iniciativa', ''),
            direccion=data.get('direccion', ''),
            institucion=data.get('institucion', ''),
            etapa_fk=Etapa.objects.get(id=data.get('etapa')) if data.get('etapa') else None,
            departamento=Departamento.objects.get(id=data.get('departamento')) if data.get('departamento') else None,
            monto_presupuestado=monto_presupuestado,
            llamado_cotizacion=data.get('llamado_cotizacion', ''),
            tipo_presupuesto=tipo_presupuesto,
            estado_fk=estado_en_curso,
            profesional_a_cargo=data.get('profesional_a_cargo', ''),
            pedido_devuelto=data.get('pedido_devuelto', False),            # Agregar la licitación fallida si se proporcionó un ID
            licitacion_fallida_linkeada=Licitacion.objects.get(id=data.get('licitacion_fallida_linkeada')) if data.get('licitacion_fallida_linkeada') else None,
        )
        licitacion.save()

        fecha_tentativa_termino = get_fecha_tentativa_termino(data.get('tipo_presupuesto', ''), licitacion.fecha_creacion.date())
        if fecha_tentativa_termino:
            try:
                licitacion.fecha_tentativa_termino = fecha_tentativa_termino
            except ValueError:
                fecha_tentativa_termino = None
        else:
            fecha_tentativa_termino = None
        licitacion.save()
          # Asignar financiamiento (ManyToMany)
        financiamiento_ids = data.get('financiamiento')
        if financiamiento_ids:
            if not isinstance(financiamiento_ids, list):
                financiamiento_ids = [financiamiento_ids]
            licitacion.financiamiento.set(financiamiento_ids)
        
        # Crear entrada en bitácora si se linkeó una licitación fallida
        if licitacion.licitacion_fallida_linkeada:
            fallida = licitacion.licitacion_fallida_linkeada
            texto_linkeo = f"Esta licitación ha sido vinculada con la licitación fallida N° {fallida.numero_pedido} - '{fallida.iniciativa}' (ID: {fallida.id})"
            
            BitacoraLicitacion.objects.create(
                licitacion=licitacion,
                texto=texto_linkeo,
                etapa=licitacion.etapa_fk
            )
            
        return JsonResponse({'ok': True, 'id': licitacion.id})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=400)

@require_POST
def eliminar_bitacora(request, bitacora_id):
    from .models import BitacoraLicitacion
    bitacora = get_object_or_404(BitacoraLicitacion, id=bitacora_id)
    bitacora.delete()
    return JsonResponse({'ok': True})

@require_GET
@login_required
def exportar_licitacion_excel(request, licitacion_id):
    """
    Exporta la licitación y/o su bitácora a Excel según el parámetro 'tipo'.
    tipo=licitacion | bitacora | ambos
    """
    tipo = request.GET.get('tipo', 'licitacion')
    licitacion = get_object_or_404(Licitacion, id=licitacion_id)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # Create workbook and header format
    workbook = writer.book
    header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})

    # Datos de la licitación
    if tipo in ['licitacion', 'ambos']:
        lic_data = {
            'ID': [licitacion.id],
            'N° Pedido': [licitacion.numero_pedido],
            'ID Mercado Público': [licitacion.id_mercado_publico or '-'],
            'N° Cuenta': [licitacion.numero_cuenta],
            'Profesional a Cargo': [licitacion.operador_user.get_full_name() if licitacion.operador_user else licitacion.operador_user.username if licitacion.operador_user else ''],
            'Tipo Licitación': [str(licitacion.tipo_licitacion) if licitacion.tipo_licitacion else ''],
            'Moneda': [str(licitacion.moneda) if licitacion.moneda else ''],
            'Categoría': [str(licitacion.categoria) if licitacion.categoria else ''],
            'Financiamiento': [', '.join([str(f) for f in licitacion.financiamiento.all()])],
            'En plan anual': ['Sí' if licitacion.en_plan_anual else 'No'],
            'Pedido devuelto': ['Sí' if licitacion.pedido_devuelto else 'No'],
            'Iniciativa': [licitacion.iniciativa],
            'Dirección': [licitacion.direccion or ''],
            'Institución': [licitacion.institucion or ''],
            'Etapa': [str(licitacion.etapa_fk) if licitacion.etapa_fk else ''],
            'Estado': [str(licitacion.estado_fk) if licitacion.estado_fk else ''],
            'Departamento': [licitacion.departamento],
            'Monto Presupuestado': [licitacion.monto_presupuestado],
            'Llamado Cotización': [licitacion.get_llamado_cotizacion_display() or ''],
            'Fecha de creación': [licitacion.fecha_creacion.strftime('%d/%m/%Y %H:%M') if licitacion.fecha_creacion else ''],
        }
        df_licit = pd.DataFrame(lic_data)
        df_licit.to_excel(writer, sheet_name='Licitacion', index=False)

        # Adjust column widths and formatting
        worksheet = writer.sheets['Licitacion']
        for i, column in enumerate(df_licit.columns):
            column_width = max(df_licit[column].astype(str).map(len).max(), len(column)) + 2
            worksheet.set_column(i, i, column_width)
        for col_num, value in enumerate(df_licit.columns.values):
            worksheet.write(0, col_num, value, header_format)

    # Bitácora
    if tipo in ['bitacora', 'ambos']:
        bitacoras = licitacion.bitacoras.all().order_by('fecha')
        bitacora_data = []
        for b in bitacoras:
            bitacora_data.append({
                'Fecha': b.fecha.strftime('%d/%m/%Y %H:%M'),
                'Etapa': str(b.etapa) if b.etapa else '',
                'Operador': str(b.operador_user) if b.operador_user else '',
                'Texto': b.texto,
                'Archivos': ', '.join([doc.nombre for doc in getattr(b, 'archivos', []).all()])
            })
        df_bit = pd.DataFrame(bitacora_data)
        df_bit.to_excel(writer, sheet_name='Bitacora', index=False)

        # Adjust column widths and formatting
        worksheet = writer.sheets['Bitacora']
        for i, column in enumerate(df_bit.columns):
            column_width = max(df_bit[column].astype(str).map(len).max(), len(column)) + 2
            worksheet.set_column(i, i, column_width)
        for col_num, value in enumerate(df_bit.columns.values):
            worksheet.write(0, col_num, value, header_format)

    writer.close()
    output.seek(0)
    filename = f"licitacion_{licitacion.numero_pedido}_export.xlsx"
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={filename}'
    return response

@require_GET
@login_required
def exportar_todas_licitaciones_excel(request):
    """
    Exporta todas las licitaciones a un archivo Excel.
    """
    try:
        # Obtenemos todas las licitaciones (o aplicamos filtros si existen en request.GET)
        q = request.GET.get('q')
        solo_anuales = request.GET.get('solo_anuales') == '1'
        solo_fallidas = request.GET.get('solo_fallidas') == '1'
        
        licitaciones = Licitacion.objects.all()
        
        if q:
            licitaciones = licitaciones.filter(
                models.Q(numero_pedido__icontains=q) | 
                models.Q(iniciativa__icontains=q)
            )
        
        if solo_anuales:
            licitaciones = licitaciones.filter(en_plan_anual=True)
        
        if solo_fallidas:
            # Buscar estados que puedan indicar "fallido" con diferentes variaciones
            estado_fallido = Estado.objects.filter(
                models.Q(nombre__iexact='fallido') | 
                models.Q(nombre__iexact='fallida') | 
                models.Q(nombre__icontains='fallid')
            ).first()
            if estado_fallido:
                licitaciones = licitaciones.filter(estado_fk=estado_fallido)
        
        # Ordenar las licitaciones
        licitaciones = licitaciones.order_by('-fecha_creacion')
        
        # Crear el archivo Excel
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Configuración del libro y formato del encabezado
        workbook = writer.book
        header_format = workbook.add_format({
            'bold': True, 
            'text_wrap': True, 
            'valign': 'top', 
            'fg_color': '#D7E4BC', 
            'border': 1
        })
        
        # Datos de todas las licitaciones
        licitaciones_data = []
        
        for licitacion in licitaciones:
            licitaciones_data.append({
                'ID': licitacion.id,
                'N° Pedido': licitacion.numero_pedido,
                'ID Mercado Público': licitacion.id_mercado_publico or '-',
                'Orden de compra': licitacion.orden_compra_adjudicacion or '-',
                'Fecha tentativa de término': licitacion.fecha_tentativa_termino.strftime('%d/%m/%Y') if licitacion.fecha_tentativa_termino else '',
                'N° Cuenta': licitacion.numero_cuenta,
                'Profesional a Cargo 1': licitacion.operador_user.get_full_name() if licitacion.operador_user else licitacion.operador_user.username if licitacion.operador_user else '',
                'Profesional a Cargo 2': licitacion.operador_user.get_full_name() if licitacion.operador_user else licitacion.operador_user.username if licitacion.operador_user else '',
                'Tipo Licitación': str(licitacion.tipo_licitacion) if licitacion.tipo_licitacion else '',
                'Moneda': str(licitacion.moneda) if licitacion.moneda else '',
                'Categoría': str(licitacion.categoria) if licitacion.categoria else '',
                'Financiamiento': ', '.join([str(f) for f in licitacion.financiamiento.all()]),
                'En plan anual': 'Sí' if licitacion.en_plan_anual else 'No',
                'Pedido devuelto': 'Sí' if licitacion.pedido_devuelto else 'No',
                'Iniciativa': licitacion.iniciativa,
                'Etapa': str(licitacion.etapa_fk) if licitacion.etapa_fk else '',
                'Estado': str(licitacion.estado_fk) if licitacion.estado_fk else '',
                'Departamento': str(licitacion.departamento) if licitacion.departamento else '',
                'Monto Presupuestado': licitacion.monto_presupuestado,
                'Tipo por presupuesto': str(licitacion.tipo_presupuesto) if licitacion.tipo_presupuesto else '',
                'Llamado Cotización': licitacion.get_llamado_cotizacion_display() or '',
                'Fecha de creación': licitacion.fecha_creacion.strftime('%d/%m/%Y %H:%M') if licitacion.fecha_creacion else '',
            })
        
        # Crear DataFrame y exportar a Excel
        df_licit = pd.DataFrame(licitaciones_data)
        df_licit.to_excel(writer, sheet_name='Licitaciones', index=False)
        
        # Ajustar anchos de columna y formato
        worksheet = writer.sheets['Licitaciones']
        for i, column in enumerate(df_licit.columns):
            column_width = max(df_licit[column].astype(str).map(len).max(), len(column)) + 2
            worksheet.set_column(i, i, column_width)
        for col_num, value in enumerate(df_licit.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        writer.close()
        output.seek(0)
        
        # Generar nombre del archivo con fecha actual y filtros aplicados
        fecha_actual = timezone.localtime(timezone.now()).strftime('%Y-%m-%d')
        filename_parts = ["licitaciones"]
        
        if solo_anuales:
            filename_parts.append("anuales")
        if solo_fallidas:
            filename_parts.append("fallidas")
            
        filename_parts.append(fecha_actual)
        filename = "_".join(filename_parts) + ".xlsx"
        
        # Enviar respuesta HTTP
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    except Exception as e:
        # En caso de error, mostrar un mensaje de error
        return HttpResponse(f"Error al exportar las licitaciones: {str(e)}", status=500)

@require_GET
def api_validar_numero_pedido(request):
    numero_pedido = request.GET.get('numero_pedido')
    excluir_id = request.GET.get('excluir_id')
    qs = Licitacion.objects.filter(numero_pedido=numero_pedido)
    if excluir_id:
        qs = qs.exclude(id=excluir_id)
    exists = qs.exists()
    return JsonResponse({'exists': exists})

@csrf_exempt
@require_GET
def api_ultima_observacion(request, licitacion_id):
    # Solo operadores pueden acceder
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session or 'operador_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    licitacion = Licitacion.objects.filter(id=licitacion_id).first()
    if not licitacion:
        return JsonResponse({'ok': False, 'error': 'Licitación no encontrada'}, status=404)
    
    # Buscar la última observación hecha por el operador
    ultima_operador = BitacoraLicitacion.objects.filter(licitacion=licitacion, operador_user__isnull=False).order_by('-fecha').first()
    
    operador_data = {
        'texto': ultima_operador.texto if ultima_operador else '',
        'fecha': ultima_operador.fecha.strftime('%d/%m/%Y %H:%M') if ultima_operador and ultima_operador.fecha else '',
        'archivos': []
    }
    
    if ultima_operador:
        operador_data['archivos'] = [
            {
                'nombre': doc.nombre or doc.archivo.name.split('/')[-1],
                'url': doc.archivo.url
            }
            for doc in ultima_operador.archivos.all()
        ]
    
    # Buscar la última observación del administrador (a través de ObservacionBitacora)
    ultima_admin = None
    admin_data = {
        'texto': '',
        'fecha': ''
    }
    
    # Primero, buscar la última bitácora que tenga una observación asociada
    bitacora_con_obs = BitacoraLicitacion.objects.filter(
        licitacion=licitacion,
        observacion__isnull=False
    ).order_by('-fecha').first()
    
    if bitacora_con_obs:
        try:
            observacion_admin = bitacora_con_obs.observacion;
            admin_data = {
                'texto': observacion_admin.texto,
                'fecha': observacion_admin.fecha.strftime('%d/%m/%Y %H:%M') if observacion_admin.fecha else ''
            }
        except:
            pass
            
    return JsonResponse({
        'ok': True, 
        'operador': operador_data,
        'admin': admin_data
    })

@require_GET
def api_licitaciones_fallidas(request):
    """
    API para obtener listado de licitaciones con estado fallido
    """
    # Verificar permisos
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session or 'operador_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    
    # Obtener todas las licitaciones con estado "fallido"
    estado_fallido = Estado.objects.filter(nombre__icontains='fallid').first()
    
    if not estado_fallido:
        return JsonResponse({'ok': False, 'error': 'No se encontró un estado que coincida con "fallido"'}, status=404)    # Obtener licitaciones fallidas
    licitaciones = Licitacion.objects.select_related('operador_user', 'etapa_fk').filter(estado_fk=estado_fallido).order_by('-id')
    
    # Convertir a formato JSON
    licitaciones_data = []
    for licitacion in licitaciones:
        # Intentar encontrar la entrada de bitácora que marca la licitación como fallida
        # Primero buscamos en el texto alguna referencia a "fallida"
        entrada_fallida = BitacoraLicitacion.objects.filter(
            licitacion=licitacion,
            texto__icontains='fallid'  # Esto buscará "fallido", "fallida", etc.
        ).order_by('-fecha').first()
        
        # Si no encontramos entrada con texto relacionado a "fallida", tomamos la última entrada
        if not entrada_fallida:
            entrada_fallida = BitacoraLicitacion.objects.filter(
                licitacion=licitacion
            ).order_by('-fecha').first()
        
        fecha_fallo = entrada_fallida.fecha.strftime('%d/%m/%Y %H:%M') if entrada_fallida and entrada_fallida.fecha else '-'
        fecha_creacion = licitacion.fecha_creacion.strftime('%d/%m/%Y %H:%M') if licitacion.fecha_creacion else '-'
        
        operador_name = '-'
        if licitacion.operador_user:
            operador_name = licitacion.operador_user.get_full_name() or licitacion.operador_user.username
        
        licitaciones_data.append({
            'id': licitacion.id,
            'numero_pedido': licitacion.numero_pedido,
            'iniciativa': licitacion.iniciativa,
            'operador_nombre': operador_name,
            'etapa_nombre': licitacion.etapa_fk.nombre if licitacion.etapa_fk else '-',
            'fecha_creacion': fecha_creacion,
            'fecha_fallo': fecha_fallo
        })
    return JsonResponse({
        'ok': True,
        'licitaciones': licitaciones_data
    })

@csrf_exempt
def api_linkear_licitacion_fallida(request):
    """
    API para linkear una licitación fallida a una nueva licitación
    Método POST
    Parámetros:
    - licitacion_id: ID de la licitación nueva
    - licitacion_fallida_id: ID de la licitación fallida a linkear
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no soportado'}, status=405)
    
    # Verificar permisos
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session or 'operador_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    
    try:
        data = json.loads(request.body)
        licitacion_id = data.get('licitacion_id')
        licitacion_fallida_id = data.get('licitacion_fallida_id')
        
        if not licitacion_id or not licitacion_fallida_id:
            return JsonResponse({'ok': False, 'error': 'Faltan parámetros requeridos'}, status=400)
        
        # Obtener la licitación
        try:
            licitacion = Licitacion.objects.get(id=licitacion_id)
        except Licitacion.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'La licitación no existe'}, status=404)
        
        # Obtener la licitación fallida
        try:
            licitacion_fallida = Licitacion.objects.get(id=licitacion_fallida_id)
        except Licitacion.DoesNotExist:
            return JsonResponse({'ok': False, 'error': 'La licitación fallida no existe'}, status=404)
        
        # Linkear la licitación fallida
        licitacion.licitacion_fallida_linkeada = licitacion_fallida
        licitacion.save()
        
        # Crear entrada en bitácora cuando se linkea una licitación fallida
        texto_linkeo = f"Esta licitación ha sido vinculada con la licitación fallida N° {licitacion_fallida.numero_pedido} - '{licitacion_fallida.iniciativa}' (ID: {licitacion_fallida.id})"
        
        BitacoraLicitacion.objects.create(
            licitacion=licitacion,
            texto=texto_linkeo,
            etapa=licitacion.etapa_fk
        )
        
        return JsonResponse({
            'ok': True,
            'mensaje': 'Licitación fallida vinculada correctamente',
            'licitacion_id': licitacion.id,
            'licitacion_fallida_id': licitacion_fallida.id
        })
        
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@csrf_exempt
def actualizar_etapa_api(request, licitacion_id):
    """
    Endpoint AJAX para actualizar la etapa de una licitación.
    Espera POST con {etapa_id, accion, crear_entrada_bitacora} y retorna JSON con el nombre de la nueva etapa.
    """
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    try:
        data = json.loads(request.body)
        etapa_id = data.get('etapa_id')
        accion = data.get('accion', 'cambio')  # 'avanzar', 'retroceder', o 'cambio'
        crear_entrada_bitacora = data.get('crear_entrada_bitacora', False)
        
        if not etapa_id:
            return JsonResponse({'ok': False, 'error': 'Falta etapa_id'}, status=400)
            
        licitacion = Licitacion.objects.get(id=licitacion_id)
        etapa_anterior = licitacion.etapa_fk
        nueva_etapa = Etapa.objects.get(id=etapa_id)
        
        # Verificar que la etapa a la que se quiere cambiar esté habilitada
        etapas_habilitadas = licitacion.get_etapas_habilitadas()
        etapas_habilitadas_ids = [rel.etapa.id for rel in etapas_habilitadas]
        
        if nueva_etapa.id not in etapas_habilitadas_ids:
            return JsonResponse({
                'ok': False, 
                'error': f'La etapa "{nueva_etapa.nombre}" está inhabilitada para esta licitación (UF < 500)'
            }, status=400)
        
        # Actualizar la etapa
        licitacion.etapa_fk = nueva_etapa
        licitacion.save()
        
        # Obtener información del operador activo después del cambio
        operador_activo = licitacion.get_operador_activo()
        numero_operador_activo = licitacion.get_numero_operador_activo()
        
        entrada_creada = False
        
        # Crear entrada automática en la bitácora si se solicita
        if crear_entrada_bitacora:
            from .models import BitacoraLicitacion
            
            # Determinar el texto del comentario según la acción
            if accion == 'avanzar':
                texto_comentario = f"🚀 Etapa avanzada automáticamente"
            elif accion == 'retroceder':
                texto_comentario = f"⬅️ Etapa retrocedida automáticamente"
            else:
                texto_comentario = f"🔄 Etapa modificada automáticamente"
            
            # Agregar información sobre el cambio
            if etapa_anterior:
                texto_comentario += f" de '{etapa_anterior.nombre}' a '{nueva_etapa.nombre}'"
            else:
                texto_comentario += f" a '{nueva_etapa.nombre}'"
            
            texto_comentario += f" desde el modal de cronología."
            
            # Obtener el operador actual (admin que realiza el cambio)
            operador_user = None
            if hasattr(request, 'user') and request.user.is_authenticated:
                operador_user = request.user
            
            
            # Crear la entrada en la bitácora
            BitacoraLicitacion.objects.create(
                licitacion=licitacion,
                operador_user=operador_user,
                texto=texto_comentario,
                etapa=nueva_etapa
            )
            entrada_creada = True
        
        return JsonResponse({
            'ok': True, 
            'etapa': {'id': nueva_etapa.id, 'nombre': nueva_etapa.nombre},
            'operador_activo': {
                'id': operador_activo.id if operador_activo else None,
                'nombre': operador_activo.get_full_name() if operador_activo else None,
                'username': operador_activo.username if operador_activo else None,
                'numero': numero_operador_activo
            },
            'entrada_bitacora_creada': entrada_creada
        })
        
    except Licitacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Licitación no encontrada'}, status=404)
    except Etapa.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Etapa no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@login_required
@require_GET
def obtener_notificaciones_api(request):
    """Obtener notificaciones no leídas para el admin"""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.rol != 'admin':
        return JsonResponse({'ok': False, 'error': 'Acceso denegado'}, status=403)
    
    # Obtener las últimas 10 notificaciones no leídas
    from .models import Notificacion
    notificaciones = Notificacion.objects.filter(leida=False).order_by('-fecha')[:10]
    
    data = []
    for notif in notificaciones:
        operador_name = notif.operador_user.get_full_name() if notif.operador_user else None
        if not operador_name and notif.operador_user:
            operador_name = notif.operador_user.username
            
        data.append({
            'id': notif.id,
            'tipo': notif.tipo,
            'titulo': notif.titulo,
            'mensaje': notif.mensaje,
            'licitacion_id': notif.licitacion.id if notif.licitacion else None,
            'licitacion_numero': notif.licitacion.numero_pedido if notif.licitacion else None,
            'operador': operador_name,
            'fecha': notif.fecha.strftime('%d/%m/%Y %H:%M'),
            'fecha_relativa': tiempo_relativo(notif.fecha)
        })
    
    total_no_leidas = Notificacion.objects.filter(leida=False).count()
    
    return JsonResponse({
        'ok': True,
        'notificaciones': data,
        'total_no_leidas': total_no_leidas
    })

@login_required
@csrf_exempt
def marcar_notificacion_leida(request, notificacion_id):
    """Marcar una notificación como leída"""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.rol != 'admin':
        return JsonResponse({'ok': False, 'error': 'Acceso denegado'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)

    
    try:
        from .models import Notificacion
        notificacion = Notificacion.objects.get(id=notificacion_id)
        notificacion.leida = True
        notificacion.save()
        
        return JsonResponse({'ok': True})
    except Notificacion.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Notificación no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@login_required
@csrf_exempt
def marcar_todas_notificaciones_leidas(request):
    """Marcar todas las notificaciones como leídas"""
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.rol != 'admin':
        return JsonResponse({'ok': False, 'error': 'Acceso denegado'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'error': 'Método no permitido'}, status=405)
    
    try:
        from .models import Notificacion
        Notificacion.objects.filter(leida=False).update(leida=True)
        
        return JsonResponse({'ok': True})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

def tiempo_relativo(fecha):
    """Devuelve tiempo transcurrido en formato relativo"""
    from django.utils import timezone
    import datetime
    
    ahora = timezone.now()
    diferencia = ahora - fecha
    
    if diferencia.days > 0:
        return f"hace {diferencia.days} día{'s' if diferencia.days > 1 else ''}"
    elif diferencia.seconds >= 3600:
        horas = diferencia.seconds // 3600
        return f"hace {horas} hora{'s' if horas > 1 else ''}"
    elif diferencia.seconds >= 60:
        minutos = diferencia.seconds // 60
        return f"hace {minutos} minuto{'s' if minutos > 1 else ''}"
    else:
        return "hace unos segundos"

@login_required
def calendario_actividad(request):
    """Vista para mostrar el calendario de actividad"""
    # Verificar que sea admin
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.rol != 'admin':
        return HttpResponseForbidden("Acceso denegado")
    
    # Obtener años disponibles para el filtro
    años_licitaciones = Licitacion.objects.dates('fecha_creacion', 'year')
    años_bitacoras = BitacoraLicitacion.objects.dates('fecha', 'year')
    
    años_disponibles = set()
    for fecha in años_licitaciones:
        años_disponibles.add(fecha.year)
    for fecha in años_bitacoras:
        años_disponibles.add(fecha.year)
    
    años_disponibles = sorted(list(años_disponibles), reverse=True)
    
    # Obtener notificaciones no leídas
    notificaciones_no_leidas = Notificacion.objects.filter(
        leida=False
    ).order_by('-fecha')[:50]
    
    contexto = {
        'es_admin': True,
        'años_disponibles': años_disponibles,
        'año_actual': timezone.now().year,
        'mes_actual': timezone.now().month,
        'notificaciones': notificaciones_no_leidas,
        'notificaciones_count': notificaciones_no_leidas.count(),
    }
    
    return render(request, 'licitaciones/calendario_actividad.html', contexto)

@require_GET
def obtener_eventos_calendario(request):
    """API para obtener eventos de fechas clave del calendario"""
    # Verificar que sea admin
    perfil = getattr(request.user, 'perfil', None)
    if not perfil or perfil.rol != 'admin':
        return JsonResponse({'ok': False, 'error': 'Acceso denegado'}, status=403)
    
    try:
        # Obtener parámetros de fecha
        año = int(request.GET.get('año', timezone.now().year))
        mes = request.GET.get('mes', None)
        if mes:
            mes = int(mes)
        
        eventos = []
        
        # Calcular rangos de fecha (Objetos datetime conscientes de zona horaria)
        if mes:
            fecha_inicio = timezone.make_aware(datetime(año, mes, 1))
            if mes == 12:
                fecha_fin = timezone.make_aware(datetime(año + 1, 1, 1))
            else:
                fecha_fin = timezone.make_aware(datetime(año, mes + 1, 1))
        else:
            fecha_inicio = timezone.make_aware(datetime(año, 1, 1))
            fecha_fin = timezone.make_aware(datetime(año + 1, 1, 1))

        # Convertimos a .date() para comparar con DateFields en la BD
        date_inicio = fecha_inicio.date()
        date_fin = fecha_fin.date()

        # Configuración de los campos que queremos buscar
        # (Nombre Campo BD, Título Evento, Color, Icono)
        campos_config = [
            ('fecha_cierre_preguntas_publicacionportal', 'Cierre Preguntas Portal', '#ffc107', '❓'), # Amarillo
            ('fecha_respuesta_publicacionportal', 'Respuestas Portal', '#17a2b8', '💬'),      # Cyan
            ('fecha_cierre_oferta_publicacionportal', 'Cierre Ofertas Portal', '#dc3545', '🛑'),   # Rojo
            ('fecha_estimada_adjudicacion_publicacionportal', 'Est. Adjudicación', '#007bff', '🏆'), # Azul
            ('fecha_cierre_ofertas_mercado_publico', 'Cierre Ofertas MP', '#fd7e14', '🛒'),     # Naranja
            ('fecha_tope_firma_contrato', 'Tope Firma Contrato', '#28a745', '✍️'),          # Verde
        ]

        # 1. Construir consulta dinámica (OR)
        # Buscamos licitaciones donde AL MENOS UNA de las fechas caiga en el rango
        query = Q()
        for campo, _, _, _ in campos_config:
            # campo__range incluye los extremos, restamos 1 día al fin para que sea exacto al mes
            query |= Q(**{f"{campo}__range": (date_inicio, date_fin - timedelta(days=1))})

        # 2. Ejecutar consulta
        licitaciones = Licitacion.objects.filter(query).select_related('operador_user')

        # 3. Procesar resultados
        for lic in licitaciones:
            # Revisamos cada campo configurado para ver si esta licitación tiene fecha en este mes
            for campo_bd, titulo_evento, color_evento, icono in campos_config:
                fecha_valor = getattr(lic, campo_bd, None)
                
                if fecha_valor and date_inicio <= fecha_valor < date_fin:
                    # Crear el evento
                    eventos.append({
                        'tipo': 'vencimiento',
                        'fecha': fecha_valor.strftime('%Y-%m-%d'),
                        'hora': '23:59', # Asumimos final del día para plazos
                        'titulo': f"{icono} {titulo_evento}",
                        'descripcion': f"Licitación: {lic.numero_pedido or 'S/N'}\nIniciativa: {lic.iniciativa or '---'}\nOperador: {lic.operador_user or 'Sin asignar'}",
                        'operador': str(lic.operador_user) if lic.operador_user else 'Sistema',
                        'etapa': str(lic.etapa_fk) if lic.etapa_fk else 'Sin etapa',
                        'licitacion_id': lic.id,
                        'color': color_evento
                    })

        # Ordenar eventos por fecha
        eventos.sort(key=lambda x: x['fecha'])
        
        return JsonResponse({
            'ok': True, 
            'eventos': eventos, 
            'total': len(eventos)
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)

@csrf_exempt
@require_GET
def api_puede_retroceder_etapa(request, licitacion_id):
    """
    API para verificar si el operador puede retroceder etapa.
    Se elimina la verificación de tipo de usuario operador: permite usuarios
    autenticados o sesiones manuales/legacy.
    """
    # Permitir acceso si está autenticado o existe sesión manual/legacy
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session or 'operador_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)
    
    licitacion = Licitacion.objects.filter(id=licitacion_id).first()
    if not licitacion:
        return JsonResponse({'ok': False, 'error': 'Licitación no encontrada'}, status=404)
    
    # Obtener el "operador" actual: prefiera el user autenticado, si no usar sesiones
    operador_user = request.user if request.user.is_authenticated else None
    if not operador_user and 'operador_manual_id' in request.session:
        operador_user = User.objects.filter(id=request.session['operador_manual_id']).first()
    if not operador_user and 'operador_id' in request.session:
        operador_user = User.objects.filter(id=request.session['operador_id']).first()
    
    if not operador_user:
        return JsonResponse({'ok': False, 'puede_retroceder': False})
    
    # Buscar la última observación del operador para esta licitación
    ultima_bitacora = BitacoraLicitacion.objects.filter(
        licitacion=licitacion, 
        operador_user=operador_user
    ).order_by('-fecha').first()
    
    puede_retroceder = True
    
    if ultima_bitacora and ultima_bitacora.texto:
        texto_lower = ultima_bitacora.texto.lower()
        if 'avance automático de etapa' in texto_lower or 'avanzar etapa' in texto_lower:
            puede_retroceder = False
    
    return JsonResponse({
        'ok': True, 
        'puede_retroceder': puede_retroceder,
        'razon': 'La última observación avanzó etapa' if not puede_retroceder else 'Puede retroceder'
    })

@csrf_exempt
@require_GET
def api_puede_avanzar_etapa(request, licitacion_id):
    """
    API para verificar si el operador puede avanzar etapa.
    Solo requiere usuario autenticado o sesión manual; no se verifica rol de operador.
    """
    # Permitir acceso si está autenticado o existe sesión manual/legacy
    if not (request.user.is_authenticated or 'operador_manual_id' in request.session or 'operador_id' in request.session):
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    licitacion = Licitacion.objects.filter(id=licitacion_id).first()
    if not licitacion:
        return JsonResponse({'ok': False, 'error': 'Licitación no encontrada'}, status=404)

    # Obtener el "operador" actual: prefiera el user autenticado, si no usar operador_manual_id de sesión
    operador_user = request.user if request.user.is_authenticated else None
    if not operador_user and 'operador_manual_id' in request.session:
        operador_user = User.objects.filter(id=request.session['operador_manual_id']).first()

    if not operador_user:
        return JsonResponse({'ok': False, 'puede_avanzar': False})

    # Buscar la etapa de última observación del usuario para esta licitación
    ultima_bitacora = BitacoraLicitacion.objects.filter(
        licitacion=licitacion,
        operador_user=operador_user
    ).order_by('-etapa').values_list('etapa', flat=True).first()

    puede_avanzar = False
    try:
        if ultima_bitacora and licitacion.etapa_fk and ultima_bitacora >= licitacion.etapa_fk.id:
            puede_avanzar = True
    except Exception:
        puede_avanzar = False

    return JsonResponse({
        'ok': True,
        'puede_avanzar': puede_avanzar,
        'ultima_bitacora': ultima_bitacora,
    })
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Departamento
import json

def crear_departamento_ajax(request):
    """Vista auxiliar para crear departamentos desde el formulario vía AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nombre_nuevo = data.get('nombre')
            
            if not nombre_nuevo:
                return JsonResponse({'error': 'Falta el nombre'}, status=400)

            # Crea el departamento o recupera uno si ya existe con ese nombre
            departamento, created = Departamento.objects.get_or_create(
                nombre=nombre_nuevo.strip() # strip quita espacios extra
            )
            
            return JsonResponse({
                'id': departamento.id,
                'nombre': departamento.nombre,
                'nuevo': created
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from .models import Licitacion

@login_required
def licitacion_info_general(request, licitacion_id):
    try:
        lic = Licitacion.objects.select_related(
            "departamento",
            "etapa_fk",
            "estado_fk",
            "tipo_licitacion",
            "operador_user",
            "operador_2"
        ).get(pk=licitacion_id)
    except Licitacion.DoesNotExist:
        raise Http404("Licitación no encontrada")

    return JsonResponse({
        "id": lic.id,
        "iniciativa": lic.iniciativa,
        "numero_pedido": lic.numero_pedido,
        "departamento": lic.departamento.nombre if lic.departamento else "-",
        "operador_1": lic.operador_user.get_full_name() if lic.operador_user else "-",
        "operador_2": lic.operador_2.get_full_name() if lic.operador_2 else "-",
        "estado": lic.estado_fk.nombre if lic.estado_fk else "-",
        "etapa": lic.etapa_fk.nombre if lic.etapa_fk else "-",
        "tipo_licitacion": lic.tipo_licitacion.nombre if lic.tipo_licitacion else "-",
        "monto": lic.monto_presupuestado,
        "moneda": lic.moneda.nombre if lic.moneda else "-",
        "en_plan_anual": "Sí" if lic.en_plan_anual else "No",
    })
