/**
 * Calendario de Actividad - Funcionalidades
 */

(function() {
    'use strict';

    // Variables globales
    let eventosData = [];
    let eventosFiltrados = [];
    let vistaActual = 'calendario'; // 'calendario' o 'lista'
    let añoActual, mesActual;

    // Elementos del DOM
    let selectAño, selectMes, btnFiltrar, btnHoy;
    let btnMesAnterior, btnMesSiguiente;
    let btnVistaCalendario, btnVistaLista;
    let vistaCalendario, vistaLista;
    let calendarioContainer, listaEventos;
    let totalEventos, totalCreaciones, totalCambiosEtapa, totalObservaciones;
    let buscarEventos, filtroTipoEvento;
    let modalEvento, cerrarModalEvento;

    // Meses en español
    const meses = [
        'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];

    const diasSemana = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];

    // Inicialización
    function inicializar() {
        obtenerElementosDOM();
        configurarEventListeners();
        inicializarFechas();
        cargarEventos();
    }

    function obtenerElementosDOM() {
        selectAño = document.getElementById('selectAño');
        selectMes = document.getElementById('selectMes');
        btnFiltrar = document.getElementById('btnFiltrar');
        btnHoy = document.getElementById('btnHoy');
        btnMesAnterior = document.getElementById('btnMesAnterior');
        btnMesSiguiente = document.getElementById('btnMesSiguiente');
        
        btnVistaCalendario = document.getElementById('btnVistaCalendario');
        btnVistaLista = document.getElementById('btnVistaLista');
        
        vistaCalendario = document.getElementById('vistaCalendario');
        vistaLista = document.getElementById('vistaLista');
        
        calendarioContainer = document.getElementById('calendarioContainer');
        listaEventos = document.getElementById('listaEventos');
        
        totalEventos = document.getElementById('totalEventos');
        totalCreaciones = document.getElementById('totalCreaciones');
        totalCambiosEtapa = document.getElementById('totalCambiosEtapa');
        totalObservaciones = document.getElementById('totalObservaciones');
        
        buscarEventos = document.getElementById('buscarEventos');
        filtroTipoEvento = document.getElementById('filtroTipoEvento');
        
        modalEvento = document.getElementById('modalEvento');
        cerrarModalEvento = document.getElementById('cerrarModalEvento');
    }

    function configurarEventListeners() {
        // Filtros
        btnFiltrar.addEventListener('click', cargarEventos);
        btnHoy.addEventListener('click', irAHoy);
        
        // Navegación de meses
        btnMesAnterior.addEventListener('click', mesAnterior);
        btnMesSiguiente.addEventListener('click', mesSiguiente);
        
        // Cambio de vista
        btnVistaCalendario.addEventListener('click', () => cambiarVista('calendario'));
        btnVistaLista.addEventListener('click', () => cambiarVista('lista'));
        
        // Filtros de lista
        buscarEventos.addEventListener('input', filtrarEventosLista);
        filtroTipoEvento.addEventListener('change', filtrarEventosLista);
        
        // Modal
        cerrarModalEvento.addEventListener('click', cerrarModal);
        modalEvento.addEventListener('click', (e) => {
            if (e.target === modalEvento) cerrarModal();
        });
        
        // Acciones del modal
        document.getElementById('btnVerLicitacion').addEventListener('click', verLicitacion);
        document.getElementById('btnVerBitacora').addEventListener('click', verBitacora);
    }

    function inicializarFechas() {
        const hoy = new Date();
        añoActual = parseInt(selectAño.value) || hoy.getFullYear();
        
        // Si no hay mes seleccionado, usar el mes actual
        if (!selectMes.value) {
            selectMes.value = hoy.getMonth() + 1;
        }
        mesActual = parseInt(selectMes.value);
    }

    function irAHoy() {
        const hoy = new Date();
        selectAño.value = hoy.getFullYear();
        selectMes.value = hoy.getMonth() + 1;
        cargarEventos();
    }

    function mesAnterior() {
        const añoActual = parseInt(selectAño.value);
        const mesActual = parseInt(selectMes.value) || new Date().getMonth() + 1;
        
        if (mesActual === 1) {
            selectAño.value = añoActual - 1;
            selectMes.value = 12;
        } else {
            selectMes.value = mesActual - 1;
        }
        
        cargarEventos();
    }

    function mesSiguiente() {
        const añoActual = parseInt(selectAño.value);
        const mesActual = parseInt(selectMes.value) || new Date().getMonth() + 1;
        
        if (mesActual === 12) {
            selectAño.value = añoActual + 1;
            selectMes.value = 1;
        } else {
            selectMes.value = mesActual + 1;
        }
        
        cargarEventos();
    }

    function cambiarVista(vista) {
        vistaActual = vista;
        
        if (vista === 'calendario') {
            btnVistaCalendario.classList.add('active');
            btnVistaLista.classList.remove('active');
            vistaCalendario.style.display = 'block';
            vistaLista.style.display = 'none';
            generarCalendario();
        } else {
            btnVistaCalendario.classList.remove('active');
            btnVistaLista.classList.add('active');
            vistaCalendario.style.display = 'none';
            vistaLista.style.display = 'block';
            generarListaEventos();
        }
    }

    function cargarEventos() {
        añoActual = parseInt(selectAño.value);
        mesActual = parseInt(selectMes.value) || null;
        
        mostrarCargando();
        
        const params = new URLSearchParams({
            año: añoActual
        });
        
        if (mesActual) {
            params.append('mes', mesActual);
        }
        
        fetch(`/api/calendario/eventos/?${params.toString()}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.ok) {
                    eventosData = data.eventos || [];
                    eventosFiltrados = [...eventosData];
                    actualizarEstadisticas();
                    
                    if (vistaActual === 'calendario') {
                        generarCalendario();
                    } else {
                        generarListaEventos();
                    }
                } else {
                    throw new Error(data.error || 'Error al cargar eventos');
                }
            })
            .catch(error => {
                console.error('Error al cargar eventos:', error);
                mostrarError('Error al cargar los eventos del calendario');
            });
    }

    function mostrarCargando() {
        if (vistaActual === 'calendario') {
            calendarioContainer.innerHTML = `
                <div class="calendario-cargando">
                    <div class="spinner"></div>
                    <p>Cargando calendario...</p>
                </div>
            `;
        } else {
            listaEventos.innerHTML = `
                <div class="eventos-cargando">
                    <div class="spinner"></div>
                    <p>Cargando eventos...</p>
                </div>
            `;
        }
    }

    function mostrarError(mensaje) {
        const errorHtml = `
            <div class="sin-eventos">
                <div class="sin-eventos-icono">⚠️</div>
                <p>${mensaje}</p>
            </div>
        `;
        
        if (vistaActual === 'calendario') {
            calendarioContainer.innerHTML = errorHtml;
        } else {
            listaEventos.innerHTML = errorHtml;
        }
    }

    function actualizarEstadisticas() {
        const estadisticas = {
            total: eventosData.length,
            creaciones: eventosData.filter(e => e.tipo === 'creacion').length,
            cambiosEtapa: eventosData.filter(e => e.tipo === 'cambio_etapa').length,
            observaciones: eventosData.filter(e => e.tipo === 'observacion').length + eventosData.filter(e => e.tipo === 'cierre').length
        };
        
        totalEventos.textContent = estadisticas.total;
        totalCreaciones.textContent = estadisticas.creaciones;
        totalCambiosEtapa.textContent = estadisticas.cambiosEtapa;
        totalObservaciones.textContent = estadisticas.observaciones;
    }

    function generarCalendario() {
        // Siempre generar el calendario, incluso sin eventos
        const año = añoActual;
        const mes = mesActual || new Date().getMonth() + 1;
        
        const fechaInicio = new Date(año, mes - 1, 1);
        const fechaFin = new Date(año, mes, 0);
        
        // Obtener el primer día de la semana del mes
        const primerDiaSemana = fechaInicio.getDay();
        const ultimoDia = fechaFin.getDate();
        
        // Agrupar eventos por fecha
        const eventosPorFecha = {};
        eventosData.forEach(evento => {
            if (!eventosPorFecha[evento.fecha]) {
                eventosPorFecha[evento.fecha] = [];
            }
            eventosPorFecha[evento.fecha].push(evento);
        });
        
        // Encabezado del mes
        const nombreMes = meses[mes - 1];
        let html = `
            <div class="calendario-header-mes">
                <h2>${nombreMes} ${año}</h2>
                ${eventosData.length === 0 ? '<p class="calendario-sin-eventos">No hay eventos en este período</p>' : `<p class="calendario-con-eventos">${eventosData.length} evento(s) encontrado(s)</p>`}
            </div>
            <div class="calendario-mes">
                ${diasSemana.map(dia => `<div class="calendario-header-dia">${dia}</div>`).join('')}
        `;
        
        // Días del mes anterior para completar la primera semana
        const fechaAnterior = new Date(año, mes - 1, 0);
        const diasAnterior = fechaAnterior.getDate();
        
        for (let i = primerDiaSemana - 1; i >= 0; i--) {
            const dia = diasAnterior - i;
            html += `<div class="calendario-dia otro-mes"><div class="dia-numero">${dia}</div></div>`;
        }
        
        // Días del mes actual, MAS TITULO EN CALENDARIIO
        const hoy = new Date();
        for (let dia = 1; dia <= ultimoDia; dia++) {
            const fecha = `${año}-${String(mes).padStart(2, '0')}-${String(dia).padStart(2, '0')}`;
            const eventos = eventosPorFecha[fecha] || [];
            
            const esHoy = hoy.getFullYear() === año && hoy.getMonth() + 1 === mes && hoy.getDate() === dia;
            
            html += `
                <div class="calendario-dia ${esHoy ? 'hoy' : ''}" data-fecha="${fecha}">
                    <div class="dia-numero">${dia}</div>
                    <div class="dia-eventos">
                        ${eventos.slice(0, 20).map(evento => `
                            <div class="evento-item ${evento.tipo}" data-evento='${JSON.stringify(evento).replace(/'/g, "&apos;")}'>
                                ${evento.titulo.length > 25 ? evento.titulo.substring(0, 12) + '...' : evento.titulo}
                            </div>
                        `).join('')}
                        ${eventos.length > 20  ? `<div class="eventos-contador">+${eventos.length - 20} más</div>` : ''}
                    </div>
                </div>
            `;
        }
        
        // Días del mes siguiente para completar la última semana
        const diasMostrados = primerDiaSemana + ultimoDia;
        const diasFaltantes = 42 - diasMostrados; // 6 semanas * 7 días
        
        for (let dia = 1; dia <= diasFaltantes && diasFaltantes < 7; dia++) {
            html += `<div class="calendario-dia otro-mes"><div class="dia-numero">${dia}</div></div>`;
        }
        
        html += '</div>';
        calendarioContainer.innerHTML = html;
        
        // Agregar event listeners para los eventos
        document.querySelectorAll('.evento-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const evento = JSON.parse(item.dataset.evento);
                mostrarDetalleEvento(evento);
            });
        });
        
        // Event listener para días (mostrar todos los eventos del día)
        document.querySelectorAll('.calendario-dia').forEach(dia => {
            dia.addEventListener('click', () => {
                const fecha = dia.dataset.fecha;
                if (fecha && eventosPorFecha[fecha]) {
                    mostrarEventosDia(fecha, eventosPorFecha[fecha]);
                }
            });
        });
    }

    function generarListaEventos() {
        if (eventosFiltrados.length === 0) {
            listaEventos.innerHTML = `
                <div class="sin-eventos">
                    <div class="sin-eventos-icono">📋</div>
                    <p>No hay eventos que coincidan con los filtros</p>
                </div>
            `;
            return;
        }
        
        const html = eventosFiltrados.map(evento => {
            const fechaFormateada = formatearFecha(evento.fecha);
            const tipoNombre = obtenerNombreTipo(evento.tipo);
            
            return `
                <div class="evento-lista-item" data-evento='${JSON.stringify(evento).replace(/'/g, "&apos;")}'>
                    <div class="evento-lista-header">
                        <div class="evento-lista-titulo">${evento.titulo}</div>
                        <div class="evento-lista-fecha">${fechaFormateada} ${evento.hora}</div>
                    </div>
                    <div class="evento-lista-descripcion">${evento.descripcion}</div>
                    <div class="evento-lista-meta">
                        <span class="evento-tipo-badge ${evento.tipo}">${tipoNombre}</span>
                        <span>👤 ${evento.operador}</span>
                        ${evento.etapa && evento.etapa !== 'Sin etapa' ? `<span>📍 ${evento.etapa}</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        listaEventos.innerHTML = html;
        
        // Agregar event listeners
        document.querySelectorAll('.evento-lista-item').forEach(item => {
            item.addEventListener('click', () => {
                const evento = JSON.parse(item.dataset.evento);
                mostrarDetalleEvento(evento);
            });
        });
    }

    function filtrarEventosLista() {
        const busqueda = buscarEventos.value.toLowerCase();
        const tipoFiltro = filtroTipoEvento.value;
        
        eventosFiltrados = eventosData.filter(evento => {
            const cumpleBusqueda = !busqueda || 
                evento.titulo.toLowerCase().includes(busqueda) ||
                evento.descripcion.toLowerCase().includes(busqueda) ||
                evento.operador.toLowerCase().includes(busqueda);
            
            const cumpleTipo = !tipoFiltro || evento.tipo === tipoFiltro;
            
            return cumpleBusqueda && cumpleTipo;
        });
        
        generarListaEventos();
    }

    function mostrarDetalleEvento(evento) {
        // Actualizar contenido del modal
        document.getElementById('eventoIcono').textContent = obtenerIconoTipo(evento.tipo);
        document.getElementById('eventoTitulo').textContent = evento.titulo;
        
        const fechaFormateada = formatearFecha(evento.fecha);
        document.getElementById('eventoFechaHora').textContent = `${fechaFormateada} a las ${evento.hora}`;
        document.getElementById('eventoTipo').textContent = obtenerNombreTipo(evento.tipo);
        document.getElementById('eventoOperador').textContent = evento.operador;
        document.getElementById('eventoDescripcion').textContent = evento.descripcion;
        
        // Mostrar/ocultar fila de etapa
        const etapaRow = document.getElementById('eventoEtapaRow');
        if (evento.etapa && evento.etapa !== 'Sin etapa') {
            document.getElementById('eventoEtapa').textContent = evento.etapa;
            etapaRow.style.display = 'flex';
        } else {
            etapaRow.style.display = 'none';
        }
        
        // Configurar botones de acción
        const btnVerLicitacion = document.getElementById('btnVerLicitacion');
        const btnVerBitacora = document.getElementById('btnVerBitacora');
        
        btnVerLicitacion.dataset.licitacionId = evento.licitacion_id;
        btnVerBitacora.dataset.licitacionId = evento.licitacion_id;
        
        // Mostrar modal
        modalEvento.style.display = 'flex';
    }

    function mostrarEventosDia(fecha, eventos) {
        // Crear un evento compuesto para mostrar todos los eventos del día
        const fechaFormateada = formatearFecha(fecha);
        const eventoCompuesto = {
            titulo: `Eventos del ${fechaFormateada}`,
            descripcion: eventos.map(e => `• ${e.titulo}: ${e.descripcion}`).join('\n'),
            fecha: fecha,
            hora: 'Todo el día',
            operador: `${eventos.length} evento(s)`,
            tipo: 'multiple',
            licitacion_id: eventos[0].licitacion_id // Usar el primero para referencia
        };
        
        mostrarDetalleEvento(eventoCompuesto);
    }

    function cerrarModal() {
        modalEvento.style.display = 'none';
    }

    function verLicitacion() {
        const licitacionId = document.getElementById('btnVerLicitacion').dataset.licitacionId;
        if (licitacionId) {
            window.location.href = `/?licitacion=${licitacionId}`;
        }
    }

    function verBitacora() {
        const licitacionId = document.getElementById('btnVerBitacora').dataset.licitacionId;
        if (licitacionId) {
            window.location.href = `/bitacora/${licitacionId}/`;
        }
    }

    // Funciones auxiliares
    function formatearFecha(fechaStr) {
        const fecha = new Date(fechaStr + 'T00:00:00');
        const opciones = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        return fecha.toLocaleDateString('es-ES', opciones);
    }

    function obtenerNombreTipo(tipo) {
        const tipos = {
            'creacion': 'Licitación Creada',
            'cambio_etapa': 'Cambio de Etapa',
            'observacion': 'Observación',
            'cierre': 'Cierre/Fallo',
            'multiple': 'Múltiples Eventos'
        };
        return tipos[tipo] || tipo;
    }

    function obtenerIconoTipo(tipo) {
        const iconos = {
            'creacion': '✨',
            'cambio_etapa': '📈',
            'observacion': '📝',
            'cierre': '❌',
            'multiple': '📅'
        };
        return iconos[tipo] || '📅';
    }

    // Inicializar cuando el DOM esté listo
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', inicializar);
    } else {
        inicializar();
    }

})();

