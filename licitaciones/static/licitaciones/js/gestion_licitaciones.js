let uploadedFiles = [];
// TIPO POR PRESUPUESTO
async function obtenerValor(moneda) {
    // Por defecto consultar api mindicador para obtener valores
    try {
        if (moneda.trim().toLowerCase() === 'clp') return 1;
        if (moneda.trim().toLowerCase() === 'usd') moneda = 'dolar';
        const response = await fetch(`https://mindicador.cl/api/${moneda.trim().toLowerCase()}`);
        if (!response.ok) throw new Error('Error al obtener los datos');
        const data = await response.json();
        return parseFloat(data.serie[0].valor);
    } catch (error) {
        // En su defecto usar tabla
        console.error('Problema al cargar api mindicador:', error.message);
        return {'uf': 39156.08, 'dolar': 965.64, 'dólar': 965.64, 'usd': 965.64, 'euro': 1125.59, 'eur': 1125.59, 'utm': 68647, 'clp': 1}[moneda.trim().toLowerCase()] ?? null;
    }
}

async function asignarTipoPresupuesto() {
    const monedaSelect = document.getElementById('monedaSelect');
    const monedaSelected = monedaSelect.options[monedaSelect.selectedIndex];
    const monto = parseFloat(document.getElementById('montoPresupuestadoInput').value);
    const tipoPresupuesto = document.getElementById('tipoPresupuesto');
    
    if (monedaSelected.value && monto > 0) {
        const valorUTM = await obtenerValor('utm');
        if (!valorUTM) {
            console.log('Error en función obtenerValor');
            return;
        }

        let montoConvertido = monto;
        if (monedaSelected.text === 'CLP') {
            if (valorUTM) montoConvertido = monto / valorUTM;
        } else if (monedaSelected.text === 'UTM') {
            montoConvertido = monto;
        } else {
            // Otras monedas: convierte primero moneda a CLP y luego a UF
            const valorMoneda = await obtenerValor(monedaSelected.text.trim().toLowerCase==='usd' ? 'dolar' : monedaSelected.text);
            if (valorMoneda && valorUTM) montoConvertido = (monto * valorMoneda) / valorUTM;
        }
        console.log(`Valor convertido en ${montoConvertido} utm`);
        // Asignar tipo según monto en UF
        if (montoConvertido < 1000) {
            tipoPresupuesto.value = 'LE';
        } else if (montoConvertido < 5000) {
            tipoPresupuesto.value = 'LP';
        } else {
            tipoPresupuesto.value = 'LR';
        }
    }
}

// --- UTILIDAD GLOBAL: Renderizar opciones de etapas en un <select> ---
async function renderEtapasSelect(select, etapas, selectedId, moneda, monto_presupuestado) {
    if (!select) return;

    select.innerHTML = '<option value="">Seleccione una etapa</option>';
    
    const getFilteredStages = async () => {
        if (!moneda || !monto_presupuestado) return etapas;
        
        try {
            const currencyName = (window.monedasLicitacion?.find(m => m.id == moneda)?.nombre) || moneda;
            const [valor, utm] = await Promise.all([obtenerValor(currencyName), obtenerValor('UTM')]);
            const threshold = 500 * utm;

            return etapas.filter(etapa => !([11,14,15,16].includes(etapa.id) && parseFloat(monto_presupuestado) * valor > threshold));
        } catch (error) {
            console.error('Error al obtener valores de divisas. Se mostrarán todas las etapas.', error);
            return etapas;
        }
    };

    const filteredEtapas = await getFilteredStages();

    filteredEtapas.forEach(etapa => {
        const opt = document.createElement('option');
        opt.value = etapa.id;
        opt.textContent = etapa.nombre;
        opt.selected = etapa.id === parseInt(selectedId);
        select.appendChild(opt);
    });
} 

// --- UTILIDAD GLOBAL: Filtrar etapas por tipo de licitación ---
function getEtapasPorTipo(tipoId) {
    if (!tipoId || !window.tiposLicitacionEtapaRaw || !window.etapasLicitacion) return window.etapasLicitacion || [];
    const ids = (window.tiposLicitacionEtapaRaw[tipoId] || []);
    if (!ids.length) return window.etapasLicitacion || [];
    // Ordenar según el orden definido en la relación
    return window.etapasLicitacion.filter(e => ids.includes(e.id));
}

const ids = ['monedaSelect', 'montoPresupuestadoInput'];
ids.forEach(id => {
    document.getElementById(id).addEventListener('change', function() {
        const hasValues = ids.every(id => {
            const el = document.getElementById(id);
            return el && el.value.trim() !== '';
        });
        if (!hasValues) return;
        asignarTipoPresupuesto();
        renderEtapasSelect(document.getElementById('etapaSelect'), getEtapasPorTipo(document.getElementById('tipoLicitacionSelect').value), document.getElementById('etapaSelect').value, document.getElementById('monedaSelect').value, document.getElementById('montoPresupuestadoInput').value);
    });
});

function getIdFromCell(cell, list, key='nombre') {
    let found = '';
    if (!cell) return '';
    const nombre = cell.innerText;
    if (!nombre || nombre === '-') return '';
        found = (window[list] || []).find(e => e.nombre === nombre);
    if (key === 'etapasLicitacion') {
        found = (list || []).find(e => e.nombre === nombre);
    }
    if (!found) {
        found = (window[list] || []).find(e => e.nombre.includes(nombre));
    }
    return found ? found.id : '';
}

async function reabrirLicitacion(idProyecto, fallida = false) {
    if (confirm(`¿Está seguro que desea reabrir esta licitación?\n\nEsta acción reabrirá la licitación y se registrará en la bitácora.`)) {
        url = `/gestion/modificar_licitacion/${idProyecto}/`;
        method = 'POST';
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
            body: JSON.stringify({estado: 1})
        })
        .then(async res => {
            if (res.ok) {
                if (fallida) {
                    // Obtener etapa actual
                    let etapaActualId;
                    let etapasLicitacion;

                     // Obtener etapa actual
                    const resEtapa = await fetch(`/api/licitacion/${idProyecto}/etapa/`);
                    if (resEtapa.ok) {
                        const dataEtapa = await resEtapa.json();
                        etapaActualId = dataEtapa.etapa_id;
                    }
                    
                    // Obtener etapas con información de inhabilitación
                    const resEtapas = await fetch(`/api/licitacion/${idProyecto}/etapas/`);
                    if (resEtapas.ok) {
                        const dataEtapas = await resEtapas.json();
                        etapasLicitacion = dataEtapas.etapas || [];
                        
                        // Mostrar información adicional si se detecta que debe saltar etapa
                        if (dataEtapas.debe_saltar_etapas) {
                            console.log(`Licitación ${licitacionId}: Saltando etapas (${dataEtapas.moneda}: ${dataEtapas.monto})`);
                        }
                    }
                    const etapasHabilitadas = etapasLicitacion.filter(e => !e.inhabilitada);
                    const etapaActualIndex = etapasHabilitadas.findIndex(e => String(e.id) === String(etapaActualId));
                    const nuevaEtapaId = etapasHabilitadas[etapaActualIndex > 0 ? etapaActualIndex - 1 : etapaActualIndex].id;
                    url = `/api/licitacion/${idProyecto}/actualizar_etapa/`;
                    method = 'POST';
                    await fetch(url, {
                        method,
                        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                        body: JSON.stringify({etapa_id: nuevaEtapaId, accion: 'retroceder'})
                    })
                    .then(res => {
                        if (res.ok){
                            // pass
                        } else {throw new Error('Error al actualizar la etapa de la licitación fallida');}
                    })
                    .catch(e => {
                        alert(e);
                    });
                }
            } else {throw new Error('Error al reabrir la licitación');}
        })
        .catch(e => {
            alert(e);
        });
        location.reload();
    }
}

// FUNCIONALIDAD DE PRUEBA: ACCIONES DINAMICAS
function initToggleAccionesDinamicas() {
    const checkboxes = document.querySelectorAll('tbody input[type="checkbox"][class="licitacion-check"]');
    const btnsAction = document.querySelectorAll('.btn-toggle-acciones');
    const toggleAcciones = document.querySelector('.toggle-acciones');
    const cerrarLicitacion = document.querySelector('.cerrar-licitacion-fila');
    const modalCerrarLicitacion = document.getElementById('modalCerrarLicitacion');
    let funCerrarLicitacionAnterior;

    function handleSingleSelection(e) {
        if (e.target.checked) {
            checkboxes.forEach(cb => {
                if (cb !== e.target) {
                    cb.checked = false;
                }
            });
            toggleAcciones.style.display="flex";
            setTimeout(() => {
                toggleAcciones.style.transform = "translateX(0)";
            }, 1);
            btnsAction.forEach(btnAction => {btnAction.dataset.id=e.target.value;});
            cerrarLicitacion.disabled=false;
            cerrarLicitacion.removeEventListener('click', funCerrarLicitacionAnterior);
            if (e.target.parentNode.parentNode !== null && e.target.parentNode.parentNode.classList.contains("lic-cerrada")){
                cerrarLicitacion.title="Reabrir licitacion";
                cerrarLicitacion.querySelector('.icono-accion').innerHTML="🔓";
                funCerrarLicitacionAnterior = () => {reabrirLicitacion(e.target.value, e.target.parentNode.parentNode.querySelector('[data-campo="estado"] .estado-badge').classList.contains("estado-fallida"))};
            } else {
                cerrarLicitacion.title="Cerrar licitación";
                cerrarLicitacion.querySelector('.icono-accion').innerHTML="🔒";
                funCerrarLicitacionAnterior = () => {modalCerrarLicitacion.style.display = 'flex';};
            }
            cerrarLicitacion.addEventListener('click', funCerrarLicitacionAnterior);
        } else {
            toggleAcciones.style.transform = "translateX(115%)";
        }
    }

    checkboxes.forEach(cb => {
        cb.addEventListener('change', handleSingleSelection);
    });
}

// Variable global para controlar el modo de operación del formulario
let modoAgregar = false;

// Función para gestionar el overflow del body
function gestionarOverflowBody() {
    const modalesAbiertos = [
        document.getElementById('modalProyecto'),
        document.getElementById('modalLicitacionesFallidas'),
        document.getElementById('modalSeleccionTipo'),
        document.getElementById('modalDocumentos'),
        document.getElementById('modalObservacion'),
        document.getElementById('modalExportarExcel'),
        document.getElementById('modalUltimaObs')
    ].filter(modal => modal && (
        modal.classList.contains('active') || 
        modal.style.display === 'flex' ||
        (modal.style.display !== 'none' && getComputedStyle(modal).display === 'flex')
    ));
    
    if (modalesAbiertos.length > 0) {
        document.body.style.overflow = 'hidden';
    } else {
        document.body.style.overflow = '';
    }
}

// Relación tipo-etapa (ordenada)
function buildTiposLicitacionEtapaRaw(raw) {
    const out = {};
    raw.forEach(rel => {
        if (!out[rel.tipo_licitacion_id]) out[rel.tipo_licitacion_id] = [];
        out[rel.tipo_licitacion_id].push({id: rel.etapa_id, orden: rel.orden});
    });
    Object.keys(out).forEach(tipoId => {
        out[tipoId] = out[tipoId].sort((a,b) => a.orden-b.orden).map(e => e.id);
    });
    return out;
}
window.tiposLicitacionEtapaRaw = buildTiposLicitacionEtapaRaw(JSON.parse(document.getElementById('tipos-licitacion-etapa-raw-data').textContent));

document.addEventListener("DOMContentLoaded", function () {
    console.log('DOM cargado - Inicializando gestión de licitaciones');
      // Verificar si debemos abrir los modales automáticamente (viniendo de la bitácora)
    const urlParams = new URLSearchParams(window.location.search);
    const shouldOpenModals = urlParams.get('open_modals') === '1';
    
    if (shouldOpenModals) {
        // Limpiar la URL para evitar que se abran los modales al refrescar
        const newUrl = window.location.pathname;
        history.pushState({}, document.title, newUrl);
        
        // Verificar si debemos abrir ambos modales (porque venimos del historial)
        if (sessionStorage.getItem('from_historial') === '1') {
            // Abrir el modal de agregar y luego el de historial
            setTimeout(() => {
                // Comprobar que los elementos existen antes de manipularlos
                if (modal && modalLicitacionesFallidas) {
                    // Primero - restablecer cualquier estado previo
                    modal.classList.remove('active', 'expanded', 'shifted-left');
                    modalLicitacionesFallidas.classList.remove('active');
                    
                    // Obtener el contenido del modal
                    const modalContent = modal.querySelector('.modal-content');
                    
                    if (modalContent) {
                        // Resetear completamente los estilos inline del modal principal primero
                        modalContent.removeAttribute('style');
                        
                        // Preparar el modal principal con su tamaño normal primero
                        // Estos valores deben coincidir con los valores por defecto del modal
                        modalContent.style.width = '80%';
                        modalContent.style.maxWidth = '1200px';
                        modalContent.style.minWidth = '750px';
                        modalContent.style.minHeight = '580px';
                        modalContent.style.maxHeight = '85vh';
                    }
                    
                    // Mostrar el modal principal primero con una pequeña pausa para garantizar la renderización
                    modal.classList.add('active');
                    
                    // Pequeña pausa antes de mostrar el historial para una mejor transición
                    setTimeout(() => {
                        // Ahora expandir el modal para hacer espacio para el historial
                        modal.classList.add('expanded');
                        
                        if (modalContent) {
                            // Aplicar estilos para modal comprimido solo después de la transición
                            modalContent.style.minHeight = '0';
                            modalContent.style.maxHeight = '48vh';
                            modalContent.style.overflowY = 'auto';
                            modalContent.style.marginBottom = '25px';
                        }
                        
                        // Mostrar el modal de historial con una pequeña pausa adicional
                        setTimeout(() => {
                            // Mostrar el modal de historial
                            modalLicitacionesFallidas.classList.add('active');
                            
                            // Actualizar estado del botón
                            if (btnVerLicitacionesFallidas) {
                                btnVerLicitacionesFallidas.classList.add('active');
                                
                                // Actualizar el icono de la flecha si existe
                                const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                                if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%) rotate(90deg)';
                            }
                            
                            // Cargar los datos de licitaciones fallidas
                            cargarLicitacionesFallidas();
                        }, 100);
                    }, 300);
                }
                
                // Limpiar el sessionStorage
                sessionStorage.removeItem('from_historial');
            }, 200);
        }
    }

    // Buscador CUANDO ESTE MAS COMPLETA LA TABLA CON DATOS CAMBIAR Y ACTUALIZAR
    function setupBuscadorLicitaciones() {
        const buscador = document.querySelector('.buscador');
        if (!buscador) return;
        buscador.addEventListener("keyup", function (e) {
            const texto = buscador.value.trim();
            if (e.key === 'Enter' && texto) {
                const url = new URL(window.location.href);
                url.searchParams.set('q', texto);
                url.searchParams.delete('page');
                window.location.href = url.toString();
            } else if (texto === '') {
                const url = new URL(window.location.href);
                url.searchParams.delete('q');
                url.searchParams.delete('page');
                window.location.href = url.toString();
            }
        });
    }

    setupBuscadorLicitaciones();

    // --- Modal y CRUD ---
    const modal = document.getElementById('modalProyecto');
    const cerrarModal = document.getElementById('cerrarModal');
    const formProyecto = document.getElementById('formProyecto');
    const btnAgregar = document.getElementById('btnAgregarLicitacion');
    const modalTitulo = document.getElementById('modalTitulo');
    const licitacionFallida = document.getElementById('licitacion-fallida');
    // AQUI SE CARGA TODO LO QUE QUIERES VER EN EDITAR QUE SE CARGO PREVIAMENTE EN BASE DATOS!
    async function abrirModal(titulo, datos = null) {
        const docsText = document.querySelector('.docs-text');
        const fileInput = document.getElementById('inputDocumentos');
        docsText.innerHTML = "📋 Formatos soportados: PDF, imágenes, Excel, Word, etc.";
        uploadedFiles = [];
        if (datos.id){
            const res = await fetch(`/api/licitacion/${datos.id}/documentos/`);
            const data = await res.json();
            if (data.licitacion_fallida){
                licitacionFallida.textContent = `Licitación fallida "${data.licitacion_fallida.iniciativa}" (N° ${data.licitacion_fallida.numero_pedido}) seleccionada`;
            } else {
                licitacionFallida.textContent = 'Historial de Licitaciones Fallidas';
            }
        } else {
            licitacionFallida.textContent = 'Historial de Licitaciones Fallidas';
        }
        modalTitulo.textContent = titulo;
        formProyecto.reset();
        limpiarSeleccionLicitacionFallida(); // Limpiar selección de licitación fallida
        // document.querySelector('field-help').innerHTML='📋 Formatos soportados: PDF, imágenes, Excel, Word, etc.';
        // Limpiar checkboxes de tipo de monto
        const montoMaximo = document.getElementById('montoMaximoCheck');
        const montoReferencial = document.getElementById('montoReferencialCheck');
        if (montoMaximo) montoMaximo.checked = false;
        if (montoReferencial) montoReferencial.checked = false;
        if (datos && datos.id) {
            document.getElementById('proyectoId').value = datos.id;
        } else {
            document.getElementById('proyectoId').value = '';
        }
        // Tipo de licitación (corrección para edición)
        if (datos && datos.tipo_licitacion) {
            const tipoLicitacionInput = document.getElementById('tipoLicitacionSelect');
            if (tipoLicitacionInput) tipoLicitacionInput.value = datos.tipo_licitacion;
        }
        // Operador 1
        if (datos && (datos.operador || datos.operador_id)) {
            const operadorSelect = document.getElementById('operadorSelect');
            if (operadorSelect) {
                // Soporta tanto id como objeto
                const opId = typeof datos.operador === 'object' ? datos.operador.id : (datos.operador_id || datos.operador);
                operadorSelect.value = opId;
            }
        }
        
        // Operador 2
        if (datos && (datos.operador_2 || datos.operador_2_id)) {
            const operador2Select = document.getElementById('operador2Select');
            if (operador2Select) {
                // Soporta tanto id como objeto
                const op2Id = typeof datos.operador_2 === 'object' ? datos.operador_2.id : (datos.operador_2_id || datos.operador_2);
                operador2Select.value = op2Id;
            }
        }
        // Etapa
        if (datos && datos.etapa) {
            const etapaSelect = document.getElementById('etapaSelect');
            if (etapaSelect) etapaSelect.value = datos.etapa;
        }
        // Moneda
        if (datos && datos.moneda) {
            const monedaSelect = document.getElementById('monedaSelect');
            if (monedaSelect) {
                monedaSelect.value = datos.moneda;
                if (!Array.from(monedaSelect.options).some(opt => opt.value == datos.moneda)) {
                    const opt = document.createElement('option');
                    opt.value = datos.moneda;
                    opt.textContent = (window.monedasLicitacion || []).find(m => m.id == datos.moneda)?.nombre || datos.moneda;
                    opt.selected = true;
                    monedaSelect.appendChild(opt);
                }
            }
        }
        // Estado
        if (datos && datos.estado) {
            const estadoSelect = document.getElementById('estadoSelect');
            if (estadoSelect) {
                estadoSelect.value = datos.estado;
                if (!Array.from(estadoSelect.options).some(opt => opt.value == datos.estado)) {
                    const opt = document.createElement('option');
                    opt.value = datos.estado;
                    opt.textContent = (window.estadosLicitacion || []).find(e => e.id == datos.estado)?.nombre || datos.estado;
                    opt.selected = true;
                    estadoSelect.appendChild(opt);
                }
            }
        }
        // Categoría
        if (datos && datos.categoria) {
            const categoriaSelect = document.getElementById('categoriaSelect');
            if (categoriaSelect) categoriaSelect.value = datos.categoria;
        }        // Financiamiento
        if (datos && datos.financiamiento) {
            const financiamientoSelect = document.getElementById('financiamientoSelect');
            if (financiamientoSelect) {
                const values = Array.isArray(datos.financiamiento) ? datos.financiamiento.map(String) : String(datos.financiamiento).split(',');
                Array.from(financiamientoSelect.options).forEach(opt => {
                    opt.selected = values.includes(String(opt.value));
                });
            }
        }
        // N° de cuenta
        const contenedorCuentas = document.getElementById('contenedorCuentas');
        if (contenedorCuentas) {
            contenedorCuentas.innerHTML = ''; 
            
            if (datos && datos.numero_cuenta) {
                // --- CORRECCIÓN AQUÍ ---
                // Antes: .split(/\s*[\/-]\s*/)  <-- Esto cortaba con guiones (-)
                // Ahora: .split(/\s*\/\s*/)     <-- Esto SOLO corta con barras (/)
                
                let cuentas = datos.numero_cuenta.split(/\s*\/\s*/); 
                
                cuentas.forEach(c => {
                    if(c.trim()) agregarFilaCuenta(c.trim());
                });
            } 
            
            if (contenedorCuentas.children.length === 0) {
                agregarFilaCuenta("");
            }
        }
        // En plan anual (select sí/no)
        if (datos && datos.en_plan_anual !== undefined) {
    const enPlanAnualSelect = document.getElementById('enPlanAnualSelect');
    const boxJustificacion = document.getElementById('contenedorJustificacion');
    const inputJustificacion = document.getElementById('justificacionInput');

    if (enPlanAnualSelect) {
        // Determinamos si es True o False (aceptando 'sí', 'si', true, 'True')
        const esSi = ['Sí', 'si', 'true', true].includes(String(datos.en_plan_anual).toLowerCase());
        enPlanAnualSelect.value = esSi ? 'True' : 'False';

        // Lógica de visualización al cargar
        if (esSi) {
            boxJustificacion.style.display = 'block';
            inputJustificacion.required = true;
            // SI TIENES EL DATO DE JUSTIFICACIÓN EN TU JSON, CARGALO AQUÍ:
            // inputJustificacion.value = datos.justificacion || ''; 
        } else {
            boxJustificacion.style.display = 'none';
            inputJustificacion.required = false;
        }
    }
}
        // Pedido devuelto (checkbox)
        if (datos && datos.pedido_devuelto !== undefined) {
            const pedidoDevueltoCheck = document.getElementById('pedidoDevueltoCheckbox');
            if (pedidoDevueltoCheck) {
                pedidoDevueltoCheck.checked = datos.pedido_devuelto === true || datos.pedido_devuelto === 'True' || datos.pedido_devuelto === true;
            }
        }
        // Llamado cotización
        if (datos && datos.llamado_cotizacion !== undefined) {
            const llamadoCotizacionSelect = document.getElementById('llamadoCotizacionSelect');
            if (llamadoCotizacionSelect) llamadoCotizacionSelect.value = datos.llamado_cotizacion;
        }

        const inputCreacion = document.getElementById('fechaCreacionInput');
    
    if (inputCreacion) {
        // ¿Es edición? Verificamos si hay ID
        const esEdicion = datos && (datos.id || datos.pk);

        if (esEdicion) {
            // ============================================
            // MODO EDICIÓN: LIBRE
            // ============================================
            inputCreacion.disabled = false; // Aseguramos que esté libre
            inputCreacion.removeAttribute('disabled'); // Doble seguridad

            // Lógica para poner el valor de la fecha
            if (datos.fecha_creacion) {
                let fechaRaw = datos.fecha_creacion.trim();
                
                if (fechaRaw.includes('T')) {
                    inputCreacion.value = fechaRaw.split('T')[0];
                } else if (fechaRaw.includes('/') || fechaRaw.includes('-')) {
                    // Conversión DD-MM-YYYY a YYYY-MM-DD
                    let separador = fechaRaw.includes('/') ? '/' : '-';
                    let partes = fechaRaw.split(separador);
                    if (partes.length === 3) {
                        // Asumiendo formato chile: dia-mes-año -> año-mes-dia
                        inputCreacion.value = `${partes[2]}-${partes[1]}-${partes[0]}`;
                    } else {
                        inputCreacion.value = fechaRaw;
                    }
                } else {
                    inputCreacion.value = fechaRaw;
                }
            }

        } else {
            // ============================================
            // MODO CREACIÓN: BLOQUEADO (Aquí lo bloqueamos por JS)
            // ============================================
            
            // 1. Bloquear
            inputCreacion.disabled = true;
            
            // 2. Poner fecha de hoy por defecto
            const hoy = new Date();
            const dia = String(hoy.getDate()).padStart(2, '0');
            const mes = String(hoy.getMonth() + 1).padStart(2, '0');
            const anio = hoy.getFullYear();
            inputCreacion.value = `${anio}-${mes}-${dia}`;
        }
    }
        // N° de pedido
        if (numeroPedidoInput) {
    // Si viene texto sucio "1050-RRHH...", parseInt lo convierte en "1050"
    numeroPedidoInput.value = parseInt(datos.numero_pedido); 
}
        // ID Mercado Público
        if (datos && datos.id_mercado_publico !== undefined) {
            const idMercadoPublicoInput = document.getElementById('idMercadoPublicoInput');
            if (idMercadoPublicoInput) idMercadoPublicoInput.value = datos.id_mercado_publico;
        }
        // Iniciativa
        if (datos && datos.iniciativa !== undefined) {
            const iniciativaInput = formProyecto['iniciativa'];
            if (iniciativaInput) iniciativaInput.value = datos.iniciativa;
        }
        // Dirección
        if (datos && datos.direccion !== undefined) {
            const direccionInput = formProyecto['direccion'];
            if (direccionInput) direccionInput.value = datos.direccion;
        }
        // Institución
        if (datos && datos.institucion !== undefined) {
            const institucionInput = formProyecto['institucion'];
            if (institucionInput) institucionInput.value = datos.institucion;
        }
        // Departamento
        if (datos && datos.departamento !== undefined) {
            const departamentoInput = formProyecto['departamento'];
            if (departamentoInput) departamentoInput.value = datos.departamento;
        }
        if (datos && datos.profesional_a_cargo !== undefined) {
            const profCargoInput = document.getElementById('profesionalCargoInput');
            if (profCargoInput) {
                profCargoInput.value = datos.profesional_a_cargo;
            }
        }
        // Monto presupuestado
        if (datos && datos.monto_presupuestado !== undefined) {
            const montoInput = formProyecto['monto_presupuestado'];
            if (montoInput) montoInput.value = datos.monto_presupuestado;
        }
        // Tipo por presupuesto
        if (datos && datos.tipo_presupuesto !== undefined) {
            const tipo_presupuesto = formProyecto['tipo_presupuesto'];
            if (tipo_presupuesto) tipo_presupuesto.value = datos.tipo_presupuesto;
        }


        if (datos && datos.fecha_tentativa_termino !== undefined) {
            const fecha_tentativa_termino = formProyecto['fecha_tentativa_termino'];
            if (fecha_tentativa_termino) fecha_tentativa_termino.value = datos.fecha_tentativa_termino;
        }

        if (datos && datos.fecha_cierre_preguntas !== undefined) {
            const fecha_cierre_preguntas = formProyecto['fecha_cierre_preguntas'];
            if (fecha_cierre_preguntas) fecha_cierre_preguntas.value = datos.fecha_cierre_preguntas;
        }

        if (datos && datos.fecha_respuesta !== undefined) {
            const fecha_respuesta = formProyecto['fecha_respuesta'];
            if (fecha_respuesta) fecha_respuesta.value = datos.fecha_respuesta;
        }

        if (datos && datos.fecha_visita_terreno !== undefined) {
            const fecha_visita_terreno = formProyecto['fecha_visita_terreno'];
            if (fecha_visita_terreno) fecha_visita_terreno.value = datos.fecha_visita_terreno;
        }

        if (datos && datos.fecha_cierre_oferta !== undefined) {
            const fecha_cierre_oferta = formProyecto['fecha_cierre_oferta'];
            if (fecha_cierre_oferta) fecha_cierre_oferta.value = datos.fecha_cierre_oferta;
        }

        if (datos && datos.fecha_apertura_tecnica !== undefined) {
            const fecha_apertura_tecnica = formProyecto['fecha_apertura_tecnica'];
            if (fecha_apertura_tecnica) fecha_apertura_tecnica.value = datos.fecha_apertura_tecnica;
        }

        if (datos && datos.fecha_apertura_economica !== undefined) {
            const fecha_apertura_economica = formProyecto['fecha_apertura_economica'];
            if (fecha_apertura_economica) fecha_apertura_economica.value = datos.fecha_apertura_economica;
        }


        // Tipo de monto (checkboxes)
        if (datos && datos.tipo_monto) {
            const montoMaximo = document.getElementById('montoMaximoCheck');
            const montoReferencial = document.getElementById('montoReferencialCheck');
            if (montoMaximo) {
                montoMaximo.checked = datos.tipo_monto === 'maximo';
            }
            if (montoReferencial) {
                montoReferencial.checked = datos.tipo_monto === 'referencial';
            }
        } else {
            // Limpiar checkboxes si no hay datos
            const montoMaximo = document.getElementById('montoMaximoCheck');
            const montoReferencial = document.getElementById('montoReferencialCheck');
            if (montoMaximo) montoMaximo.checked = false;
            if (montoReferencial) montoReferencial.checked = false;
        }
        // Tipo de licitación
        let tipoLicitacionId = '';
        if (datos && datos.tipo_licitacion) tipoLicitacionId = datos.tipo_licitacion;
        else {
            const tipoInput = document.getElementById('tipoLicitacionSelect');
            if (tipoInput) tipoLicitacionId = tipoInput.value;
        }
        // Filtrar etapas por tipo de licitación
        const etapaSelect = document.getElementById('etapaSelect');
        let etapasFiltradas = getEtapasPorTipo(tipoLicitacionId);        // Etapa: preseleccionar la etapa de la licitación
        let etapaSeleccionada = '';
        if (datos && datos.etapa) etapaSeleccionada = datos.etapa;
        if (datos.moneda && datos.monto_presupuestado && etapasFiltradas.length > 0) {
            renderEtapasSelect(etapaSelect, etapasFiltradas, etapaSeleccionada, datos.moneda, datos.monto_presupuestado);
        }
        else {
            renderEtapasSelect(etapaSelect, etapasFiltradas, etapaSeleccionada);
        }
        modal.classList.add('active');
        gestionarOverflowBody();
        asignarTipoPresupuesto();
        // Asegurar que el select de etapas quede con el valor correcto
        if (etapaSeleccionada) etapaSelect.value = etapaSeleccionada;

        const selectPlan = document.getElementById('enPlanAnualSelect');
    const boxJustificacion = document.getElementById('contenedorJustificacion');
    const inputJustificacion = document.getElementById('justificacionInput');

    if (selectPlan && boxJustificacion && inputJustificacion) {
        
        // Función auxiliar para mostrar/ocultar
        const toggleJustificacion = (valor) => {
             // Convertimos a string para comparar fácil
            const valStr = String(valor).toLowerCase();
            
            // Si es 'true', 'sí', 'si' o '1' -> MOSTRAMOS
            if (['true', 'sí', 'si', '1'].includes(valStr)) {
                boxJustificacion.style.display = 'block';
                inputJustificacion.required = true;
            } else {
                boxJustificacion.style.display = 'none';
                inputJustificacion.required = false;
            }
        };

        // 2. Establecemos el valor inicial que viene de la base de datos (variable 'datos')
        // IMPORTANTE: Aquí usamos la variable 'datos' que fallaba antes
        if (datos && datos.en_plan_anual !== undefined) {
            
            // Normalizamos para saber si es True o False
            let esSi = ['Sí', 'si', 'true', true, 1].includes(datos.en_plan_anual);
            // Caso especial si viene como string "True"
            if(String(datos.en_plan_anual).toLowerCase() === 'true') esSi = true;

            const valorFinal = esSi ? 'True' : 'False';
            
            // Asignamos al select y ejecutamos la visualización
            selectPlan.value = valorFinal;
            toggleJustificacion(valorFinal);
            
            // (Opcional) Si tienes el texto de la justificación guardado en 'datos', cárgalo aquí:
             if (datos.justificacion_plan) {
                inputJustificacion.value = datos.justificacion_plan;
            } else {
                inputJustificacion.value = ''; // Limpia el campo si no hay texto
            }
        }

        // 3. Detectamos cuando TÚ cambias el select manualmente
        selectPlan.onchange = function() {
            toggleJustificacion(this.value);
        };
    }
    // ---------------------------------------------------------
    // FIN LÓGICA PLAN ANUAL
    // ---------------------------------------------------------
    }

    const modalSeleccionTipo = document.getElementById('modalSeleccionTipo');
    const cerrarModalSeleccionTipo = document.getElementById('cerrarModalSeleccionTipo');
    const btnCancelarSeleccionTipo = document.getElementById('btnCancelarSeleccionTipo');
    const btnContinuarSeleccionTipo = document.getElementById('btnContinuarSeleccionTipo');
    const selectTipoLicitacion = document.getElementById('selectTipoLicitacion');    const etapaSelect = document.getElementById('etapaSelect');
    const labelEtapa = etapaSelect?.closest('label');

    // --- MODAL SELECCIÓN TIPO DE LICITACIÓN Y ETAPA AUTOMÁTICA ---
    // La variable modoAgregar ahora es global
    
    // Verifica si el botón agregar existe antes de añadir el event listener
    if (btnAgregar) {
        btnAgregar.addEventListener('click', () => {
            console.log('Botón Agregar Licitación clickeado');
            const modalSeleccionTipo = document.getElementById('modalSeleccionTipo');
            const selectTipoLicitacion = document.getElementById('selectTipoLicitacion');
              if (modalSeleccionTipo && selectTipoLicitacion) {
                selectTipoLicitacion.value = '';
                modalSeleccionTipo.classList.add('active');
                gestionarOverflowBody();
                modoAgregar = true;
            } else {
                console.error('modalSeleccionTipo o selectTipoLicitacion no encontrado', { 
                    modalSeleccionTipo: !!modalSeleccionTipo, 
                    selectTipoLicitacion: !!selectTipoLicitacion 
                });
            }
        });
    } else {
        console.error('Botón Agregar Licitación no encontrado');    }

    // Cerrar modal selección tipo
    if (cerrarModalSeleccionTipo) {
        cerrarModalSeleccionTipo.onclick = function() { 
            modalSeleccionTipo.classList.remove('active'); 
            modoAgregar = false;
            gestionarOverflowBody();
        };
    }
    if (btnCancelarSeleccionTipo) btnCancelarSeleccionTipo.onclick = function() { 
        modalSeleccionTipo.classList.remove('active'); 
        modoAgregar = false;
        gestionarOverflowBody();
    };
    window.addEventListener('click', function(event) {
        if (event.target === modalSeleccionTipo) { 
            modalSeleccionTipo.classList.remove('active'); 
            modoAgregar = false;
            gestionarOverflowBody();
        }
    });
    // Continuar: abrir modal de agregar licitación con tipo seleccionado y etapa automática
    if (btnContinuarSeleccionTipo) btnContinuarSeleccionTipo.onclick = function() {
        const tipoId = selectTipoLicitacion.value;
        if (!tipoId) {
            alert('Selecciona un tipo de licitación.');
            return;
        }
        // Buscar la primera etapa asociada a este tipo
        let primeraEtapaId = '';
        if (window.tiposLicitacionEtapaRaw && window.tiposLicitacionEtapaRaw[tipoId] && window.tiposLicitacionEtapaRaw[tipoId].length > 0) {
            primeraEtapaId = window.tiposLicitacionEtapaRaw[tipoId][0];
        } else if (window.etapasLicitacion && window.etapasLicitacion.length > 0) {
            primeraEtapaId = window.etapasLicitacion[0].id;
        }
        // Ocultar el campo de etapa en el modal de agregar
        if (labelEtapa) labelEtapa.style.display = 'none';        // Abrir el modal de agregar licitación, pasando el tipo y la etapa
        abrirModal('Agregar Licitación', { tipo_licitacion: tipoId, etapa: primeraEtapaId });
        modalSeleccionTipo.classList.remove('active');
        modoAgregar = true;
        gestionarOverflowBody();
    };
    // Al cerrar el modal de agregar licitación, volver a mostrar el campo de etapa
    function restaurarCampoEtapa() {
        if (labelEtapa) labelEtapa.style.display = '';
        etapaSelect.disabled = false;
        // Eliminar input hidden si existe
        let hiddenEtapa = formProyecto.querySelector('input[name="etapa"]');
        if (hiddenEtapa && etapaSelect) {
            // Solo eliminar si el select existe (no en forms de observación)
            hiddenEtapa.remove();
        }
    }    if (cerrarModal) {        cerrarModal.addEventListener('click', () => { 
            restaurarCampoEtapa();
            modoAgregar = false;
            
            // También cerrar el modal de fallidas si está abierto primero
            if (modalLicitacionesFallidas.classList.contains('active')) {
                modalLicitacionesFallidas.classList.remove('active');
                
                // Resetear estado del botón de toggle
                if (btnVerLicitacionesFallidas) {
                    btnVerLicitacionesFallidas.classList.remove('active');
                    
                    // Resetear también el icono de la flecha
                    const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                    if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
                }
            }
            
            // Luego cerrar el modal principal con una pequeña pausa
            setTimeout(() => {
                modal.classList.remove('expanded'); // Primero quitar la expansión
                
                // Restaurar cualquier estilo inline aplicado al contenido del modal
                const modalContent = modal.querySelector('.modal-content');
                if (modalContent) {
                    // Restaurar altura máxima y estilo de scroll
                    modalContent.style.minHeight = '';
                    modalContent.style.maxHeight = '';
                    modalContent.style.overflowY = '';
                    modalContent.style.marginBottom = '';
                    modalContent.style.width = '';
                    modalContent.style.minWidth = '';
                }
                  // Por último quitar la clase active y shifted-left
                modal.classList.remove('active', 'shifted-left');
                
                // Restaurar el overflow del body después de cerrar todos los modales
                gestionarOverflowBody();
            }, 100);
        });
    }    if (btnCancelar) {btnCancelar.addEventListener('click', () => {
            restaurarCampoEtapa();
            modoAgregar = false;
            
            // También cerrar el modal de fallidas si está abierto primero
            if (modalLicitacionesFallidas.classList.contains('active')) {
                modalLicitacionesFallidas.classList.remove('active');
                
                // Resetear estado del botón de toggle
                if (btnVerLicitacionesFallidas) {
                    btnVerLicitacionesFallidas.classList.remove('active');
                    
                    // Resetear también el icono de la flecha
                    const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                    if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
                }
            }
            
            // Luego cerrar el modal principal con una pequeña pausa
            setTimeout(() => {
                modal.classList.remove('expanded'); // Primero quitar la expansión
                
                // Restaurar cualquier estilo inline aplicado al contenido del modal
                const modalContent = modal.querySelector('.modal-content');
                if (modalContent) {
                    // Restaurar altura máxima y estilo de scroll
                    modalContent.style.minHeight = '';
                    modalContent.style.maxHeight = '';
                    modalContent.style.overflowY = '';
                    modalContent.style.marginBottom = '';
                    modalContent.style.width = '';
                    modalContent.style.minWidth = '';
                }
                  // Por último quitar la clase active y shifted-left
                modal.classList.remove('active', 'shifted-left');
                
                // Restaurar el overflow del body después de cerrar todos los modales
                gestionarOverflowBody();
            }, 100);
        });
    }    window.onclick = function(event) {
        if (event.target == modal) { 
            restaurarCampoEtapa(); 
            modoAgregar = false; 
            
            // También cerrar el modal de fallidas si está abierto primero
            if (modalLicitacionesFallidas.classList.contains('active')) {
                modalLicitacionesFallidas.classList.remove('active');
                
                // Resetear estado del botón de toggle
                if (btnVerLicitacionesFallidas) {
                    btnVerLicitacionesFallidas.classList.remove('active');
                    
                    // Resetear también el icono de la flecha
                    const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                    if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
                }
            }
            
            // Luego cerrar el modal principal con una pequeña pausa
            setTimeout(() => {
                modal.classList.remove('expanded'); // Primero quitar la expansión
                
                // Restaurar cualquier estilo inline aplicado al contenido del modal
                const modalContent = modal.querySelector('.modal-content');
                if (modalContent) {
                    // Restaurar altura máxima y estilo de scroll
                    modalContent.style.minHeight = '';
                    modalContent.style.maxHeight = '';
                    modalContent.style.overflowY = '';
                    modalContent.style.marginBottom = '';
                    modalContent.style.width = '';
                    modalContent.style.minWidth = '';
                }
                  // Por último quitar la clase active y shifted-left
                modal.classList.remove('active', 'shifted-left');
                
                // Restaurar el overflow del body después de cerrar todos los modales
                gestionarOverflowBody();
            }, 100);
              // También cerrar el modal de fallidas si está abierto
            if (modalLicitacionesFallidas.classList.contains('active')) {
                modalLicitacionesFallidas.classList.remove('active');
                
                // Resetear estado del botón de toggle
                if (btnVerLicitacionesFallidas) {
                    btnVerLicitacionesFallidas.classList.remove('active');
                }
            }
        }
    };

    // ---  EDITAR  ---
document.querySelectorAll('.editar-fila').forEach(btn => {
    btn.addEventListener('click', function() {
        const id = this.getAttribute('data-id');
        
        // Buscar la fila correspondiente por data-id en la tabla principal
        const fila = document.querySelector(`tbody tr[data-id="${id}"]`);
        
        // Validar que se encontró la fila
        if (!fila) {
            console.error('No se pudo encontrar la fila correspondiente para el botón editar con ID:', id);
            return;
        }
        
        function parseChileanNumber(str) {
            if (!str) return '';
            str = str.replace(/[$\s]/g, '');
            str = str.replace(/\./g, '').replace(/,/g, '.');
            return str;
        }
        
        // Obtener los operadores desde las celdas actualizadas con badges
        const operadoresCell = fila.querySelector('[data-campo="operadores"]');
        let operadorId = '';
        let operador2Id = '';
        
        if (operadoresCell) {
            // Buscar los badges de operadores para extraer la información
            const operador1Badge = operadoresCell.querySelector('.operador-1');
            const operador2Badge = operadoresCell.querySelector('.operador-2');
            
            // Para obtener los IDs reales, necesitamos buscar en la lista de operadores
            // Extraer nombres de los badges
            if (operador1Badge) {
                const texto1 = operador1Badge.textContent.replace('OP1: ', '').trim();
                if (texto1 !== 'No asignado') {
                    const operador1 = (window.operadoresLicitacion || []).find(op => 
                        op.full_name === texto1 || op.username === texto1
                    );
                    if (operador1) operadorId = operador1.id;
                }
            }
            if (operador2Badge && !operador2Badge.classList.contains('no-asignado')) {
                const texto2 = operador2Badge.textContent.replace('OP2: ', '').trim();
                if (texto2 !== 'No asignado') {
                    const operador2 = (window.operadoresLicitacion || []).find(op => 
                        op.full_name === texto2 || op.username === texto2
                    );
                    if (operador2) operador2Id = operador2.id;
                }
            }
        }
        const fechaCreacionCell = fila.querySelector('[data-campo="fecha_creacion"]');
        const etapaCell = fila.querySelector('[data-campo="etapa"]');
        const estadoBadge = fila.querySelector('[data-campo="estado"] .estado-badge');
        const monedaCell = fila.querySelector('[data-campo="moneda"]');
        const categoriaCell = fila.querySelector('[data-campo="categoria"]');
        const financiamientoCell = fila.querySelector('[data-campo="financiamiento"]');
        const numeroCuentaCell = fila.querySelector('[data-campo="numero_cuenta"]');
        const enPlanAnualCell = fila.querySelector('[data-campo="en_plan_anual"]');
        const pedidoDevueltoCell = fila.querySelector('[data-campo="pedido_devuelto"]');
        const iniciativaCell = fila.querySelector('[data-campo="iniciativa"]');
        const departamentoCell = fila.querySelector('[data-campo="departamento"]');
        const montoCell = fila.querySelector('[data-campo="monto_presupuestado"]');
        const llamadoCotizacionCell = fila.querySelector('[data-campo="llamado_cotizacion"]');
        const numeroPedidoCell = fila.querySelector('[data-campo="numero_pedido"]');
        const idMercadoPublicoCell = fila.querySelector('[data-campo="id_mercado_publico"]');
        const direccionCell = fila.querySelector('[data-campo="direccion"]');
        const institucionCell = fila.querySelector('[data-campo="institucion"]');
        const tipoPresupuestoCell = fila.querySelector('[data-campo="tipo_presupuesto"]');

        // Utilidad para obtener el id real por nombre
        function getIdFromCell(cell, list, key='nombre') {
            let found = '';
            if (!cell) return '';
            const nombre = cell.innerText;
            if (!nombre || nombre === '-') return '';
                found = (window[list] || []).find(e => e.nombre === nombre);
            if (key === 'etapasLicitacion') {
                found = (list || []).find(e => e.nombre === nombre);
            }
            if (!found) {
                found = (window[list] || []).find(e => e.nombre.includes(nombre));
            }
            return found ? found.id : '';
        }
        
        // Utilidad para obtener el key de choices por display value
        function getKeyFromChoiceDisplay(cell, choicesMap) {
            if (!cell) return '';
            const display = cell.innerText.trim();
            if (!display || display === '-') return '';
            // Buscar en el mapa de choices el key que corresponde al display
            for (const [key, value] of Object.entries(choicesMap || {})) {
                if (value === display) {
                    return key;
                }
            }
            return '';
        }
        
        // Mapeo de choices para llamado_cotizacion
        const llamadoCotizacionChoices = {
            'primer_llamado': 'Primer llamado',
            'segundo_llamado': 'Segundo llamado',
            'tercer_llamado': 'Tercer llamado',
            'cuarto_llamado': 'Cuarto llamado',
            'quinto_llamado': 'Quinto llamado'
        };
        // Obtener todos los IDs de financiamiento de la celda
        function getIdsFromFinanciamientoCell(cell) {
            if (!cell) return [];
            
            // Obtener el texto completo de la celda
            let textoCompleto = cell.innerText.trim();
            
            // Si es solo un guión, retornar array vacío
            if (textoCompleto === '-') return [];
            
            // Dividir por ' / ' ya que ese es el separador usado en el template
            const nombres = textoCompleto.split(' / ').map(nombre => nombre.trim()).filter(nombre => nombre && nombre !== '-');
            
            // Buscar los IDs correspondientes en window.financiamientosLicitacion
            return nombres.map(nombre => {
                const found = (window.financiamientosLicitacion || []).find(e => e.nombre === nombre);
                return found ? String(found.id) : null;
            }).filter(Boolean);
        }
        // Estado
        let estadoValue = '';
        if (estadoBadge) {
            const nombreEstado = estadoBadge.textContent.trim();
            const foundEstado = (window.estadosLicitacion || []).find(e => e.nombre === nombreEstado);
            if (foundEstado) estadoValue = foundEstado.id;
        }
        abrirModal('Editar Licitación', {
            id: id,
            operador: operadorId || '',
            operador_2: operador2Id || '',
            fecha_creacion: fechaCreacionCell ? fechaCreacionCell.innerText.trim().split(' ')[0] : '',
            etapa: getIdFromCell(etapaCell, getEtapasPorTipo(getIdFromCell(fila.querySelector('[data-campo="tipo_licitacion"]'), 'tiposLicitacion')), 'etapasLicitacion'),
            estado: estadoValue,
            moneda: getIdFromCell(monedaCell, 'monedasLicitacion'),
            categoria: getIdFromCell(categoriaCell, 'categoriasLicitacion'),
            financiamiento: getIdsFromFinanciamientoCell(financiamientoCell),
            numero_cuenta: numeroCuentaCell ? numeroCuentaCell.innerText.trim() : '',
            en_plan_anual: enPlanAnualCell ? (enPlanAnualCell.innerText.trim().toLowerCase() === 'sí' ? 'True' : 'False') : '',
            justificacion_plan: enPlanAnualCell ? enPlanAnualCell.getAttribute('data-justificacion') : '',
            pedido_devuelto: pedidoDevueltoCell ? (pedidoDevueltoCell.innerText.trim().toLowerCase() === 'sí' ? true : false) : false,
            iniciativa: iniciativaCell ? iniciativaCell.innerText.trim() : '',
            departamento: getIdFromCell(departamentoCell, 'departamentosLicitacion'),
            monto_presupuestado: montoCell ? parseChileanNumber(montoCell.innerText.replace(/[^0-9.,-]/g, '')) : '',
            tipo_presupuesto: tipoPresupuestoCell ? tipoPresupuestoCell.innerText : '',
            llamado_cotizacion: getKeyFromChoiceDisplay(llamadoCotizacionCell, llamadoCotizacionChoices),
            numero_pedido: numeroPedidoCell ? numeroPedidoCell.innerText.trim() : '',
            id_mercado_publico: idMercadoPublicoCell ? (idMercadoPublicoCell.innerText.trim() === '-' ? '' : idMercadoPublicoCell.innerText.trim()) : '',
            direccion: direccionCell ? (direccionCell.innerText.trim() === '-' ? '' : direccionCell.innerText.trim()) : '',
            institucion: institucionCell ? (institucionCell.innerText.trim() === '-' ? '' : institucionCell.innerText.trim()) : '',
            tipo_licitacion: getIdFromCell(fila.querySelector('[data-campo="tipo_licitacion"]'), 'tiposLicitacion'),
            profesional_a_cargo: fila.querySelector('[data-campo="profesional_a_cargo"]') ? fila.querySelector('[data-campo="profesional_a_cargo"]').textContent.trim() : '',
            
        });
    });
});

document.querySelectorAll('.eliminar-fila').forEach(btn => {
    btn.addEventListener('click', async function() {
        const id = this.getAttribute('data-id');
        if (!confirm('¿Seguro que deseas eliminar este proyecto?')) return;
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const res = await fetch(`/gestion/eliminar_licitacion/${id}/`, { method: 'POST', headers: { 'X-CSRFToken': csrftoken } });
        if (res.ok) location.reload();
        else alert('Error al eliminar el proyecto');
    });
});

// --- DOCUMENTOS: mostrar y subir archivos ---
const modalDocumentos = document.getElementById('modalDocumentos');
const cerrarModalDocumentos = document.getElementById('cerrarModalDocumentos');
const listaDocumentosContainer = document.getElementById('listaDocumentosContainer');
// Mostrar modal de documentos al hacer click en 📎
document.querySelectorAll('.documentos-fila').forEach(btn => {
    btn.addEventListener('click', async function() {
        const licitacionId = this.getAttribute('data-id');
        listaDocumentosContainer.innerHTML = '<div style="text-align:center;">Cargando...</div>';        modalDocumentos.style.display = 'flex';
        gestionarOverflowBody();
        // Obtener documentos por AJAX
        try {
            const res = await fetch(`/api/licitacion/${licitacionId}/documentos/`);
            const data = await res.json();
            
            // Crear contenido HTML
            let contenidoHTML = '';
            
            // Mostrar licitación fallida vinculada si existe
            if (data.licitacion_fallida) {
                const fallida = data.licitacion_fallida;
                contenidoHTML += `

                <div style="margin-bottom:20px; padding:15px; border:1px solid #f8d7da; background-color:#f8f9fa; border-radius:8px;">
                    <h3 style="color:#dc3545; margin-top:0; font-size:16px; display:flex; align-items:center; justify-content:space-between;">
                        <span>Licitación Fallida Vinculada</span>                        <a href="${fallida.url_bitacora}" class="btn icon-btn" style="background:#0275d8; margin:0 2px; display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px; border-radius:4px;" title="Ver bitácora">
                            <span class="icono-accion">📒</span>
                        </a>
                    </h3>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-top:10px;">
                        <div><strong>N° de pedido:</strong> ${fallida.numero_pedido}</div>
                        <div><strong>Iniciativa:</strong> ${fallida.iniciativa || '-'}</div>
                        <div><strong>Profesional a cargo:</strong> ${fallida.operador}</div>
                        <div><strong>Etapa:</strong> ${fallida.etapa}</div>
                        <div><strong>Fecha de creación:</strong> ${fallida.fecha_creacion}</div>
                        <div><strong>Fecha de fallo:</strong> ${fallida.fecha_fallo}</div>
                    </div>
                </div>`;
            }
            
            // Agregar documentos si existen
            if (data.ok && data.documentos.length) {
                contenidoHTML += '<h3 style="color:#0275d8; margin-top:5px; font-size:16px;">Documentos</h3>';
                contenidoHTML += '<ul style="padding:0;list-style:none;">' +
                    data.documentos.map(doc => {
                        let origenLabel = '';
                        if (doc.origen === 'bitacora') {
                            origenLabel = `<span style='background:#f0ad4e;color:#222;padding:2px 7px;border-radius:4px;font-size:0.92em;margin-left:8px;'>Bitácora</span>`;
                        } else {
                            origenLabel = `<span style='background:#5bc0de;color:#fff;padding:2px 7px;border-radius:4px;font-size:0.92em;margin-left:8px;'>Licitación</span>`;
                        }
                        let bitacoraInfo = '';
                        if (doc.origen === 'bitacora') {
                            bitacoraInfo = `<div style='font-size:0.93em;color:#888;margin-top:2px;'>Comentario: ${doc.bitacora_texto ? doc.bitacora_texto.substring(0, 60) : ''}...<br>Fecha bitácora: ${doc.bitacora_fecha}</div>`;
                        }
                        return `<li>
                            <div class="doc-info">
                                <a href='${doc.url}' target='_blank' style='font-weight:bold;color:#0275d8;text-decoration:underline;'>${doc.nombre}</a>
                                <span style='font-size:0.9em;color:#888;'>(${doc.fecha_subida})</span>
                                <span class="bitacora-label">${origenLabel}</span>
                                ${bitacoraInfo}
                            </div>
                            <div class="doc-actions">
                                <a href='${doc.url}' download class='btn descargar-btn' title='Descargar archivo'>⬇️ Descargar</a>
                            </div>
                        </li>`;
                    }).join('') + '</ul>';
            } else if (!data.licitacion_fallida) {
                // Solo mostrar mensaje de sin documentos si tampoco hay licitación fallida
                contenidoHTML += '<div style="text-align:center;">Sin documentos subidos.</div>';
            }
            
            // Actualizar el contenido del modal
            listaDocumentosContainer.innerHTML = contenidoHTML;
        } catch (e) {
            console.error('Error al cargar documentos:', e);
            listaDocumentosContainer.innerHTML = '<div style="color:red;text-align:center;">Error al cargar documentos</div>';
        }
        // Evento para eliminar archivo de la lista
        setTimeout(() => {
            document.querySelectorAll('.eliminar-doc-btn').forEach(btn => {
                btn.onclick = async function() {
                    if (!confirm('¿Seguro que deseas eliminar este archivo?')) return;
                    const docId = this.getAttribute('data-doc-id');
                    const licitacionId = this.getAttribute('data-licitacion-id');
                    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                    try {
                        const res = await fetch(`/api/licitacion/${licitacionId}/documentos/${docId}/eliminar/`, {
                            method: 'POST',
                            headers: { 'X-CSRFToken': csrftoken },
                    });
                    if (res.ok) {
                        this.closest('li').remove();
                    } else {
                        alert('Error al eliminar el archivo');
                    }
                    } catch (err) {
                        alert('Error al eliminar el archivo');
                    }
                };
            });
        }, 200);
    });
});
if (cerrarModalDocumentos) {
    cerrarModalDocumentos.onclick = function() { 
        modalDocumentos.style.display = 'none'; 
        gestionarOverflowBody();
    };
}
window.addEventListener('click', function(event) {
    if (event.target === modalDocumentos) { 
        modalDocumentos.style.display = 'none';
        gestionarOverflowBody();
    }
});
    // Controlador principal de envío del formulario
formProyecto.onsubmit = async function(e) {
    e.preventDefault();
    console.log("Formulario enviado, modoAgregar:", modoAgregar);
    
    // Primero validamos el número de pedido
    const esValido = await validarNumeroPedido();
    if (!esValido) {
        return false;
    }
    
    const datos = new FormData(formProyecto);
    const idProyecto = datos.get('id');
    let url, method;
    let datosJson = {};
    datos.forEach((v, k) => {
        if (k === 'financiamiento') {
            // Recoger todos los seleccionados como array de strings
            const values = datos.getAll('financiamiento');
            datosJson[k] = values;
        } else if (k === 'en_plan_anual') {
            datosJson[k] = v === 'True' || v === true || v === 1 || v === '1';
        } else if (k === 'pedido_devuelto') {
            datosJson[k] = v === 'True' || v === true || v === 1 || v === '1';
        } else if (k === 'tipo_licitacion' || k === 'etapa') {
            // Forzar a enviar solo un valor (el primero si por error viniera como array)
            if (Array.isArray(v)) {
                datosJson[k] = v[0];
            } else {
                datosJson[k] = v;
            }
        
        } else {
            datosJson[k] = v;
        }

    });
    
    // Agregar tipo de monto basado en los checkboxes
    const montoMaximo = document.getElementById('montoMaximoCheck');
    const montoReferencial = document.getElementById('montoReferencialCheck');
    if (montoMaximo && montoMaximo.checked) {
        datosJson['tipo_monto'] = 'maximo';
    } else if (montoReferencial && montoReferencial.checked) {
        datosJson['tipo_monto'] = 'referencial';
    }
    
    // Manejar checkbox pedido_devuelto explícitamente
    const pedidoDevueltoCheck = document.getElementById('pedidoDevueltoCheckbox');
    if (pedidoDevueltoCheck) {
        datosJson['pedido_devuelto'] = pedidoDevueltoCheck.checked;
    }
    
    // Incluir el ID de la licitación fallida seleccionada si existe
    if (licitacionFallidaSeleccionada) {
        datosJson.licitacion_fallida_id = licitacionFallidaSeleccionada.id;
    }
    
    if (idProyecto && idProyecto.trim() !== '') {
        url = `/gestion/modificar_licitacion/${idProyecto}/`;
        method = 'POST';
    } else {
        url = '/gestion/agregar_proyecto/';
        method = 'POST';
    }
    
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    let res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
        body: JSON.stringify(datosJson)
    });
    const resData = await res.json();
    if (!res.ok && resData && resData.error) {
        alert(resData.error);
        return;
    }
    
    if (res.ok && formProyecto.documentos && formProyecto.documentos.files.length > 0) {
        // Subir archivos si hay
        const formDataArchivos = new FormData();
        for (let i = 0; i < formProyecto.documentos.files.length; i++) {
            formDataArchivos.append('documentos', formProyecto.documentos.files[i]);
        }
        const idFinal = idProyecto && idProyecto.trim() !== '' ? idProyecto : resData.id;
        await fetch(`/api/licitacion/${idFinal}/documentos/subir/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            body: formDataArchivos
        });
    }
    // Antes de enviar, si el campo de etapa está oculto y es alta, poner el valor como hidden
    if (modoAgregar && labelEtapa && labelEtapa.style.display === 'none') {
        let hiddenEtapa = formProyecto.querySelector('input[name="etapa"]');
        if (!hiddenEtapa) {
            hiddenEtapa = document.createElement('input');
            hiddenEtapa.type = 'hidden';
            hiddenEtapa.name = 'etapa';
            formProyecto.appendChild(hiddenEtapa);
        }
        hiddenEtapa.value = etapaSelect.value;
        etapaSelect.disabled = true;
    } else {
        etapaSelect.disabled = false;
    }
    if (res.ok) {
        location.reload();
    } else {
        alert('Error al guardar la licitación');
    }
};

    // Cambio de operador desde el select en la tabla
    document.querySelectorAll('.operador-select').forEach(function(select) {
        select.addEventListener('change', async function() {
            const proyectoId = this.getAttribute('data-proyecto-id');
            const operadorId = this.value;
            const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
            const res = await fetch(`/gestion/modificar_licitacion/${proyectoId}/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrftoken },
                body: JSON.stringify({ operador: operadorId })
            });
            if (!res.ok) {
                alert('Error al cambiar el operador');
            }
        });
    });

    // Botón de estadísticas
    document.querySelector('.btn.estadisticas')?.addEventListener('click', function() {
        window.location.href = '/estadisticas/';
    });
    


    // --- EXPORTAR A EXCEL ---
    document.getElementById('btnExportarTodasLicitaciones')?.addEventListener('click', function() {
        console.log('Botón Exportar todas las licitaciones clickeado');
        
        // Obtener los parámetros actuales de la URL para mantener los filtros
        const currentUrl = new URL(window.location.href);
        const params = new URLSearchParams();
        
        // Copiar los filtros activos (solo_anuales, solo_fallidas)
        if (currentUrl.searchParams.get('solo_anuales') === '1') {
            params.set('solo_anuales', '1');
        }
        if (currentUrl.searchParams.get('solo_fallidas') === '1') {
            params.set('solo_fallidas', '1');
        }
        
        // Construir la URL de exportación con los parámetros
        let exportUrl = '/api/exportar_todas_licitaciones_excel/';
        if (params.toString()) {
            exportUrl += '?' + params.toString();
        }
        
        console.log('URL de exportación:', exportUrl);
        
        // Mostrar notificación de inicio
        let mensajeInicio = 'Generando archivo Excel con ';
        if (currentUrl.searchParams.get('solo_anuales') === '1' && currentUrl.searchParams.get('solo_fallidas') === '1'  && currentUrl.searchParams.get('q')) {
            mensajeInicio += 'licitaciones anuales fallidas';
        } else if (currentUrl.searchParams.get('solo_anuales') === '1') {
            mensajeInicio += 'licitaciones anuales';
        } else if (currentUrl.searchParams.get('solo_fallidas') === '1') {
            mensajeInicio += 'licitaciones fallidas';
        }  else if (currentUrl.searchParams.get('q')) {
            mensajeInicio += 'licitaciones que coinciden con la búsqueda "' + currentUrl.searchParams.get('q') + '"';
        } else {
            mensajeInicio += 'todas las licitaciones';
        }
        mensajeInicio += '...';
        
        showNotification(mensajeInicio, 'info');
        
        // Crear y ejecutar el enlace de descarga
        const link = document.createElement('a');
        link.href = exportUrl;
        
        // Generar nombre de archivo según los filtros activos
        let fileName = 'licitaciones';
        if (currentUrl.searchParams.get('solo_anuales') === '1') {
            fileName += '_anuales';
        }
        if (currentUrl.searchParams.get('solo_fallidas') === '1') {
            fileName += '_fallidas';
        }
        if (currentUrl.searchParams.get('q')) {
            fileName += `_${currentUrl.searchParams.get('q').replace(/\s+/g, '_')}`;
        } 
        fileName += '.xlsx';
        
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Mostrar notificación al usuario
        let mensaje = 'Descargando ';
        if (currentUrl.searchParams.get('solo_anuales') === '1' && currentUrl.searchParams.get('solo_fallidas') === '1' && currentUrl.searchParams.get('q')) {
            mensaje += 'licitaciones anuales fallidas que coinciden con la búsqueda "' + currentUrl.searchParams.get('q') + '"';
        } else if (currentUrl.searchParams.get('solo_anuales') === '1' && currentUrl.searchParams.get('solo_fallidas') === '1') {
            mensaje += 'licitaciones anuales fallidas';
        } else if (currentUrl.searchParams.get('solo_anuales') === '1') {
            mensaje += 'licitaciones anuales';
        } else if (currentUrl.searchParams.get('solo_fallidas') === '1') {
            mensaje += 'licitaciones fallidas';
        } else if (currentUrl.searchParams.get('q')) {
            mensajeInicio += 'licitaciones que coinciden con la búsqueda "' + currentUrl.searchParams.get('q') + '"';
        } else {
            mensaje += 'todas las licitaciones';
        }
        mensaje += ' en Excel...';
        
        showNotification(mensaje, 'success');
    });

    // --- EXPORTAR A EXCEL POR LICITACIÓN ---
    document.querySelectorAll('.exportar-excel-fila').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.stopPropagation();            const licitacionId = this.getAttribute('data-id');
            const modalExport = document.getElementById('modalExportarExcel');
            modalExport.style.display = 'flex';
            modalExport.setAttribute('data-licitacion-id', licitacionId);
        });
    });
    // Cerrar modal exportar
    document.getElementById('cerrarModalExportar').onclick = function() {
        document.getElementById('modalExportarExcel').style.display = 'none';
    };
    document.getElementById('btnCancelarExportar').onclick = function() {
        document.getElementById('modalExportarExcel').style.display = 'none';
    };
    // Enviar exportar
    document.getElementById('formExportarExcel').onsubmit = function(e) {
        e.preventDefault();
        const modal = document.getElementById('modalExportarExcel');
        const licitacionId = modal.getAttribute('data-licitacion-id');
        const option = document.querySelector('input[name="exportOption"]:checked').value;
        // Construir URL de exportación
        let url = `/api/licitacion/${licitacionId}/exportar_excel/?tipo=${option}`;
        // Descargar archivo sin redirigir ni abrir nueva pestaña
        const link = document.createElement('a');
        link.href = url;
        link.download = '';        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        document.getElementById('modalExportarExcel').style.display = 'none';
    };
    // Cerrar modal al hacer click fuera
    document.getElementById('modalExportarExcel').onclick = function(e) {
        if (e.target === this) this.style.display = 'none';
    };

    // --- OBSERVACIÓN OPERADOR ---
    // (Sección eliminada, no debe haber líneas con '-')

    // --- CRONOMETRO ---
    function setupCronometro() {
        const contadores = document.querySelectorAll('.contador-registro');
        contadores.forEach(contador => {
            const fechaStr = contador.getAttribute('data-fecha');
            if (!fechaStr) return;
            // Parsear fecha y calcular diferencia
            const fecha = new Date(fechaStr);
            const ahora = new Date();
            const diff = Math.abs(ahora - fecha);
            // Calcular días, horas y minutos
            const dias = Math.floor(diff / (1000 * 60 * 60 * 24));
            const horas = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutos = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            // Formatear cadena
            let cadena = '';
            if (dias > 0) cadena += `${dias}d `;
            if (horas > 0 || dias > 0) cadena += `${horas}h `;
            cadena += `${minutos}m`;
            contador.textContent = cadena;
        });
    }
    setupCronometro();
    setInterval(setupCronometro, 60000); // Actualizar cada minuto

    // Modal Última Observación
    const modalUltimaObs = document.getElementById('modalUltimaObs');
    const cerrarModalUltimaObs = document.getElementById('cerrarModalUltimaObs');
    const contenidoUltimaObs = document.getElementById('contenidoUltimaObs');
    const fechaUltimaObs = document.getElementById('fechaUltimaObs');
    const archivosUltimaObs = document.getElementById('archivosUltimaObs');
    document.querySelectorAll('.ultima-obs-fila').forEach(btn => {
        btn.addEventListener('click', function() {
            const licId = this.dataset.id;
            fetch(`/api/licitacion/${licId}/ultima_observacion/`)
                .then(res => res.json())
                .then(data => {
                    if (data.ok) {
                        contenidoUltimaObs.textContent = data.texto || '(Sin observaciones del operador)';
                        fechaUltimaObs.textContent = data.fecha ? `Fecha: ${data.fecha}` : '';
                        if (data.archivos && data.archivos.length > 0) {
                            archivosUltimaObs.innerHTML = '<div style="font-weight:600;margin-bottom:4px;">Archivos adjuntos:</div>' +
                                '<ul style="padding-left:18px;">' +
                                data.archivos.map(a => `<li><a href="${a.url}" target="_blank" style="color:#0275d8;text-decoration:underline;">${a.nombre}</a> <a href="${a.url}" download style="margin-left:8px;font-size:0.95em;">⬇️</a></li>`).join('') +
                                '</ul>';
                        } else {
                            archivosUltimaObs.innerHTML = '';
                        }
                    } else {
                        contenidoUltimaObs.textContent = 'No hay observaciones del operador.';
                        fechaUltimaObs.textContent = '';
                        archivosUltimaObs.innerHTML = '';
                    }
                    modalUltimaObs.style.display = 'flex';
                })
                .catch(() => {
                    contenidoUltimaObs.textContent = 'Error al obtener la observación.';
                    fechaUltimaObs.textContent = '';
                    archivosUltimaObs.innerHTML = '';
                    modalUltimaObs.style.display = 'flex';
                });
        });
    });
    if (cerrarModalUltimaObs) {
        cerrarModalUltimaObs.onclick = function() {
            modalUltimaObs.style.display = 'none';
        };
    }

    // --- FILTROS SUPERIORES ---
    document.getElementById('btnFiltrarAnuales')?.addEventListener('click', function() {
        const url = new URL(window.location.href);
        const actual = url.searchParams.get('solo_anuales');
        if (actual === '1') {
            url.searchParams.delete('solo_anuales');
        } else {
            url.searchParams.set('solo_anuales', '1');
            url.searchParams.delete('page');
        }
        window.location.href = url.toString();
    });
    
    document.getElementById('btnFiltrarFallidas')?.addEventListener('click', function() {
        const url = new URL(window.location.href);
        const actual = url.searchParams.get('solo_fallidas');
        if (actual === '1') {
            url.searchParams.delete('solo_fallidas');
        } else {
            url.searchParams.set('solo_fallidas', '1');
            url.searchParams.delete('page');
        }
        window.location.href = url.toString();
    });

    document.getElementById('btnFiltrarPedido')?.addEventListener('click', function() {
        const numeroPedido = document.getElementById('numeroPedido');
        const url = new URL(window.location.href);
        const actual = url.searchParams.get('q');
        url.searchParams.set('q', numeroPedido.value.trim());
        url.searchParams.delete('page');
        console.log('Filtro aplicado para número de pedido:', numeroPedido.value.trim());
        window.location.href = url.toString();
    });

    // Botón Mostrar Todas - Limpiar todos los filtros
    document.getElementById('btnMostrarTodas')?.addEventListener('click', function() {
        const url = new URL(window.location.href);
        // Eliminar todos los filtros
        url.searchParams.delete('solo_anuales');
        url.searchParams.delete('solo_fallidas');
        url.searchParams.delete('q');
        url.searchParams.delete('page');
        window.location.href = url.toString();
    });    // Movemos la validación al evento onsubmit principal para evitar conflictos
    // La función validarNumeroPedido se usará dentro del onsubmit
    async function validarNumeroPedido() {
        const numeroPedidoInput = document.getElementById('numeroPedidoInput');
        if (numeroPedidoInput && numeroPedidoInput.value) {
            const numeroPedido = numeroPedidoInput.value.trim();
            // Verificar si el número ya existe (excepto si es edición y no cambió)
            const idActual = document.getElementById('proyectoId').value;
            let url = `/api/validar_numero_pedido/?numero_pedido=${encodeURIComponent(numeroPedido)}`;
            if (idActual) url += `&excluir_id=${idActual}`;
            try {
                const res = await fetch(url);
                const data = await res.json();
                if (data.exists) {
                    alert('El N° de pedido ya está en uso por otra licitación. Debe ingresar uno único.');
                    numeroPedidoInput.focus();
                    return false;
                }
                return true;
            } catch (error) {
                console.error("Error validando número de pedido:", error);
                return false;
            }
        }
        return true; // Si no hay número de pedido, consideramos válido
    }

    // --- Modal de Licitaciones Fallidas ---
    const modalLicitacionesFallidas = document.getElementById('modalLicitacionesFallidas');
    const cerrarModalFallidas = document.getElementById('cerrarModalFallidas');
    const btnVerLicitacionesFallidas = document.getElementById('btnVerLicitacionesFallidas');
    const buscarLicitacionFallida = document.getElementById('buscarLicitacionFallida');
    const licitacionesFallidasBody = document.getElementById('licitacionesFallidasBody');
    const sinResultadosFallidas = document.getElementById('sinResultadosFallidas');
    
    // Variable para almacenar todas las licitaciones fallidas
    let licitacionesFallidasData = [];

    // Función para cargar las licitaciones fallidas desde el servidor
    function cargarLicitacionesFallidas() {
        fetch('/api/licitaciones/fallidas/')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error al cargar licitaciones fallidas');
                }
                return response.json();
            })
            .then(data => {
                licitacionesFallidasData = data.licitaciones || [];
                renderizarLicitacionesFallidas(licitacionesFallidasData);
            })
            .catch(error => {
                console.error('Error:', error);
                mostrarMensajeError('No se pudieron cargar las licitaciones fallidas');
            });
    }    // Función para renderizar las licitaciones fallidas en la tabla
    function renderizarLicitacionesFallidas(licitaciones) {
        if (licitaciones.length === 0) {
            licitacionesFallidasBody.innerHTML = '';
            sinResultadosFallidas.style.display = 'block';
            return;
        }

        sinResultadosFallidas.style.display = 'none';
        licitacionesFallidasBody.innerHTML = '';        licitaciones.forEach(licitacion => {
            const row = document.createElement('tr');
            row.setAttribute('data-licitacion-id', licitacion.id);
            row.innerHTML = `
                <td style="padding:10px; width:80px;">${licitacion.numero_pedido || '-'}</td>
                <td style="padding:10px; width:130px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${licitacion.iniciativa || '-'}</td>
                <td style="padding:10px; width:110px;">${licitacion.operador_nombre || '-'}</td>
                <td style="padding:10px; width:180px;">${licitacion.etapa_nombre || '-'}</td>
                <td style="padding:10px; width:110px;">${licitacion.fecha_creacion || '-'}</td>
                <td style="padding:10px; width:110px;">${licitacion.fecha_fallo || '-'}</td>
                <td style="text-align:center; padding:10px; width:80px;">
                    <a href="/bitacora/${licitacion.id}/?from_historial=1" class="btn icon-btn" style="background:#0275d8; margin:0 2px; display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px; border-radius:4px;" title="Ver bitácora" target="_blank">
                        <span class="icono-accion">📒</span>
                    </a>
                </td>                <td style="text-align:center; padding:10px; width:80px;">
                    <button class="btn icon-btn btn-seleccionar-fallida" style="background:#28a745; margin:0 2px; display:inline-flex; align-items:center; justify-content:center; width:32px; height:32px; border-radius:4px;" title="Seleccionar esta licitación fallida" data-licitacion-id="${licitacion.id}" data-iniciativa="${licitacion.iniciativa || ''}" data-num-pedido="${licitacion.numero_pedido || ''}">
                        <span class="icono-accion">✔️</span>
                    </button>
                </td>`;
            licitacionesFallidasBody.appendChild(row);
        });

        // Agregar event listeners a los botones de seleccionar después de crear las filas
        const botonesSeleccionar = licitacionesFallidasBody.querySelectorAll('.btn-seleccionar-fallida');
        botonesSeleccionar.forEach(boton => {
            boton.addEventListener('click', function() {
                const licitacionId = this.getAttribute('data-licitacion-id');
                const iniciativa = this.getAttribute('data-iniciativa');
                const numPedido = this.getAttribute('data-num-pedido');
                
                // Llamar a la función para seleccionar la licitación
                seleccionarLicitacionFallida(licitacionId, iniciativa, numPedido);

                



                


                
                const modalLicitacionesFallidas = document.getElementById('modalLicitacionesFallidas');
                const btnVerLicitacionesFallidas = document.getElementById('btnVerLicitacionesFallidas');

                // Ocultar el modal de licitaciones fallidas con animación
                modalLicitacionesFallidas.classList.remove('active');
                
                // Actualizar el icono de la flecha del botón
                if (btnVerLicitacionesFallidas) {
                    btnVerLicitacionesFallidas.classList.remove('active');
                    const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                    if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
                }
                
                // Restaurar el modal principal a su estado normal con transición
                setTimeout(() => {
                    const modalPrincipal = document.getElementById('modalProyecto');
                    modalPrincipal.classList.remove('expanded');
                    
                    const modalContent = modalPrincipal.querySelector('.modal-content');
                    if (modalContent) {
                        modalContent.style.minHeight = '580px';
                        modalContent.style.maxHeight = '85vh';
                        modalContent.style.overflowY = 'visible';
                        modalContent.style.marginBottom = '0';
                    }
                }, 200);
                
                // Restaurar el modal principal después de un breve retardo
                setTimeout(() => {
                    // Devolver el modal principal al centro
                    const modalPrincipal = document.getElementById('modalProyecto');
                    modalPrincipal.classList.remove('expanded');
                    
                    // Resetear el scroll y tamaño del contenido
                    const modalContent = modalPrincipal.querySelector('.modal-content');
                    if (modalContent) {
                        modalContent.style.minHeight = '580px';
                        modalContent.style.maxHeight = '85vh';
                        modalContent.style.overflowY = 'visible';
                        modalContent.style.marginBottom = '0';
                    }
                }, 200);
                
                // Resetear estado del botón de toggle
                if (btnVerLicitacionesFallidas) {
                    btnVerLicitacionesFallidas.classList.remove('active');
                    // Resetear también el icono de la flecha
                    const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                    if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
                }
                
                // Restaurar el overflow del body después de un breve retraso
                setTimeout(() => {
                    gestionarOverflowBody();
                }, 250);













            });
        });
    }    // Función para filtrar licitaciones fallidas por iniciativa o número de pedido
    function filtrarLicitacionesFallidas(texto) {
        if (!texto) {
            renderizarLicitacionesFallidas(licitacionesFallidasData);
            return;
        }

        const textoBusqueda = texto.toLowerCase().trim();
        const resultados = licitacionesFallidasData.filter(licitacion => {
            // Convertimos la iniciativa a string vacío si es null o undefined
            const iniciativa = (licitacion.iniciativa || '').toString().toLowerCase().trim();
            // También verificamos en el número de pedido para mejorar la búsqueda
            const numeroPedido = (licitacion.numero_pedido || '').toString().toLowerCase().trim();
            
            return iniciativa.includes(textoBusqueda) || numeroPedido.includes(textoBusqueda);
        });

        if (resultados.length === 0) {
            // Mostrar mensaje específico para búsqueda sin resultados
            mostrarMensajeError(`No se encontraron licitaciones fallidas que coincidan con "${texto}"`);
        } else {
            renderizarLicitacionesFallidas(resultados);        }
    }
    
    // Función para mostrar un mensaje de error o información
    function mostrarMensajeError(mensaje) {
        sinResultadosFallidas.textContent = mensaje;
        sinResultadosFallidas.style.display = 'block';
        licitacionesFallidasBody.innerHTML = '';
    }
      // Event Listeners para el modal de licitaciones fallidas
    if (btnVerLicitacionesFallidas) {
        btnVerLicitacionesFallidas.addEventListener('click', function() {
            // Comprobar si el modal de historial ya está abierto
            const isModalActive = modalLicitacionesFallidas.classList.contains('active');
            if (isModalActive) {
                // Si ya está abierto, lo cerramos
                modalLicitacionesFallidas.classList.remove('active');
                  // Restaurar el modal principal a su estado normal con transición
                setTimeout(() => {
                    // Devolver el modal principal al centro
                    const modalPrincipal = document.getElementById('modalProyecto');
                    modalPrincipal.classList.remove('expanded');
                    
                    // Restaurar tamaño del contenido del modal principal
                    const modalContent = modalPrincipal.querySelector('.modal-content');
                    if (modalContent) {
                        // Restaurar altura máxima y estilo de scroll
                        modalContent.style.minHeight = '580px';
                        modalContent.style.maxHeight = '85vh';
                        modalContent.style.overflowY = 'visible';
                        modalContent.style.marginBottom = '0';
                        
                        // Asegurarnos de que el fondo ocupe todo el espacio
                        document.body.style.overflow = 'hidden';
                        modalPrincipal.style.height = '100%';
                    }
                }, 200);
                
                // Cambiar estado visual del botón
                btnVerLicitacionesFallidas.classList.remove('active');
                
                // Actualizar el icono de la flecha
                const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
            } else {

                const modalPrincipal = document.getElementById('modalProyecto');

                modalPrincipal.classList.add('expanded');
                

                document.body.style.overflow = 'hidden';
                modalPrincipal.style.height = '100%';

                setTimeout(() => {
                    // Ajustar altura del contenido del modal principal antes de mostrar el historial
                    const modalContent = modalPrincipal.querySelector('.modal-content');
                    if (modalContent) {    
                        modalContent.style.minHeight = '0';
                        modalContent.style.maxHeight = '45vh'; 
                        modalContent.style.overflowY = 'auto';
                        modalContent.style.marginBottom = '40px'; 
                        

                        modalPrincipal.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                    }
    
                    setTimeout(() => {
                        modalLicitacionesFallidas.classList.add('active');
                        gestionarOverflowBody();
                        modalLicitacionesFallidas.style.width = modalContent ? 
                            `${modalContent.offsetWidth}px` : '85%';
                    }, 100);
                }, 300);
                
                // Cambiar estado visual del botón
                btnVerLicitacionesFallidas.classList.add('active');
                
                // Actualizar el icono de la flecha
                const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%) rotate(90deg)';
                
                // Cargar los datos
                cargarLicitacionesFallidas();
            }
        });
    }    if (cerrarModalFallidas) {
        cerrarModalFallidas.addEventListener('click', function() {
            // Ocultar el modal de licitaciones fallidas con animación
            modalLicitacionesFallidas.classList.remove('active');
            
            // Actualizar el icono de la flecha del botón
            if (btnVerLicitacionesFallidas) {
                btnVerLicitacionesFallidas.classList.remove('active');
                const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
            }
            
            // Restaurar el modal principal a su estado normal con transición
            setTimeout(() => {
                const modalPrincipal = document.getElementById('modalProyecto');
                modalPrincipal.classList.remove('expanded');
                
                const modalContent = modalPrincipal.querySelector('.modal-content');
                if (modalContent) {
                    modalContent.style.minHeight = '580px';
                    modalContent.style.maxHeight = '85vh';
                    modalContent.style.overflowY = 'visible';
                    modalContent.style.marginBottom = '0';
                }
            }, 200);
            
            // Restaurar el modal principal después de un breve retardo
            setTimeout(() => {
                // Devolver el modal principal al centro
                const modalPrincipal = document.getElementById('modalProyecto');
                modalPrincipal.classList.remove('expanded');
                
                // Resetear el scroll y tamaño del contenido
                const modalContent = modalPrincipal.querySelector('.modal-content');
                if (modalContent) {
                    modalContent.style.minHeight = '580px';
                    modalContent.style.maxHeight = '85vh';
                    modalContent.style.overflowY = 'visible';
                    modalContent.style.marginBottom = '0';
                }
            }, 200);
            
            // Resetear estado del botón de toggle
            if (btnVerLicitacionesFallidas) {
                btnVerLicitacionesFallidas.classList.remove('active');
                  // Resetear también el icono de la flecha
                const toggleIcon = btnVerLicitacionesFallidas.querySelector('.toggle-icon');
                if(toggleIcon) toggleIcon.style.transform = 'translateY(-50%)';
            }
            
            // Restaurar el overflow del body después de un breve retraso
            setTimeout(() => {
                gestionarOverflowBody();
            }, 250);
        });
    }
      if (buscarLicitacionFallida) {
        // Responder a eventos de input para filtrado inmediato
        buscarLicitacionFallida.addEventListener('input', function() {
            filtrarLicitacionesFallidas(this.value.trim());
        });
        
        // Permitir limpiar búsqueda con escape
        buscarLicitacionFallida.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                this.value = '';
                filtrarLicitacionesFallidas('');
            }
        });
        
        // Añadir placeholder informativo
        buscarLicitacionFallida.setAttribute('placeholder', 'Buscar por iniciativa o N° pedido...');
    }
    
    // Debug final - verificar elementos críticos
    console.log('Estado final de inicialización:', {
        modal: !!modal,
        btnAgregar: !!btnAgregar,
        modalSeleccionTipo: !!document.getElementById('modalSeleccionTipo'),
        selectTipoLicitacion: !!document.getElementById('selectTipoLicitacion')
    });
});

let licitacionFallidaSeleccionada = null; // Variable global para almacenar el ID de la licitación fallida seleccionada

// Función para limpiar la selección de licitación fallida
function limpiarSeleccionLicitacionFallida() {
    licitacionFallidaSeleccionada = null;
    const licitacionFallidaInput = document.getElementById('licitacionFallidaLinkeada');
    if (licitacionFallidaInput) {
        licitacionFallidaInput.value = '';
    }
    
    // Limpiar resaltado de filas en el modal de fallidas
    const licitacionesFallidasBody = document.getElementById('licitacionesFallidasBody');
    if (licitacionesFallidasBody) {
        const filas = licitacionesFallidasBody.querySelectorAll('tr');
        filas.forEach(fila => {
            fila.style.backgroundColor = '';
            fila.style.borderLeft = '';
        });
    }
}

// Función para seleccionar licitación fallida
function seleccionarLicitacionFallida(licitacionId, iniciativa, numPedido) {
        // Guardamos el ID de la licitación seleccionada
        licitacionFallidaSeleccionada = {
            id: licitacionId,
            iniciativa: iniciativa,
            numero_pedido: numPedido
        };
        
        // Asignar el ID al campo oculto del formulario
        const licitacionFallidaInput = document.getElementById('licitacionFallidaLinkeada');
        if (licitacionFallidaInput) {
            licitacionFallidaInput.value = licitacionId;
        }
        
        // Resaltamos la fila seleccionada
        const filas = licitacionesFallidasBody.querySelectorAll('tr');
        filas.forEach(fila => {
            fila.style.backgroundColor = '';
            fila.style.borderLeft = '';
        });
        
        const filaSeleccionada = licitacionesFallidasBody.querySelector(`tr[data-licitacion-id="${licitacionId}"]`);
        if (filaSeleccionada) {
            filaSeleccionada.style.backgroundColor = '#e3f2fd';
            filaSeleccionada.style.borderLeft = '4px solid #0275d8';
        }
        
        // Mostramos mensaje de confirmación
        mostrarNotificacion(`Licitación fallida "${iniciativa}" (N° ${numPedido}) seleccionada para linkear`, 'success');
        document.getElementById('licitacion-fallida').textContent=`Licitación fallida "${iniciativa}" (N° ${numPedido}) seleccionada`;
        
        // NO actualizar el campo iniciativa - permitir que el usuario ingrese su propia iniciativa
        // const iniciativaInput = document.querySelector('#iniciativaInput');
        // if (iniciativaInput && iniciativa) {
        //     iniciativaInput.value = iniciativa;
        // }
    
    // Opcional: se puede cerrar automáticamente el modal de fallidas después de seleccionar
    // modalLicitacionesFallidas.classList.remove('active');
}

// Función auxiliar para mostrar notificaciones
function mostrarNotificacion(mensaje, tipo = 'info') {
    // Crear el contenedor de notificación
    const notificacion = document.createElement('div');
    notificacion.className = `notificacion notificacion-${tipo}`;
    notificacion.innerHTML = mensaje;
    notificacion.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 12px 20px;
        background-color: ${tipo === 'success' ? '#d4edda' : '#cce5ff'};
        color: ${tipo === 'success' ? '#155724' : '#004085'};
        border: 1px solid ${tipo === 'success' ? '#c3e6cb' : '#b8daff'};
        border-radius: 5px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        z-index: 9999;
        opacity: 0;
        transform: translateY(-10px);
        transition: all 0.3s ease;
    `;
    
    // Añadir al cuerpo del documento
    document.body.appendChild(notificacion);
    
    // Mostrar con animación
    setTimeout(() => {
        notificacion.style.opacity = '1';
        notificacion.style.transform = 'translateY(0)';
    }, 10);
    
    // Eliminar después de 3 segundos
    setTimeout(() => {
        notificacion.style.opacity = '0';
        notificacion.style.transform = 'translateY(-10px)';
        setTimeout(() => {
            document.body.removeChild(notificacion);
        }, 300);
    }, 3000);
}

// ===== MEJORAS PARA EL MODAL MODERNO =====

// Función para inicializar las mejoras del modal moderno
function initModernModalEnhancements() {
    const modal = document.getElementById('modalProyecto');
    const modalContent = modal?.querySelector('.modal-content');
    const form = document.getElementById('formProyecto');
    
    if (!modal || !modalContent || !form) return;
    
    // Configurar animaciones de entrada/salida
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                const isActive = modal.classList.contains('active');
                
                if (isActive) {
                    // Modal se está abriendo
                    modalContent.style.animation = 'modalFadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards';
                } else {
                    // Modal se está cerrando
                    modalContent.style.animation = 'modalFadeOut 0.3s cubic-bezier(0.4, 0, 0.2, 1) forwards';
                }
            }
        });
    });
    
    observer.observe(modal, { attributes: true });
    
    // Mejorar la experiencia de drag and drop
    initFileUploadEnhancements();
    
    // Agregar validación en tiempo real
    initFormValidation();
    
    // Mejorar la experiencia de navegación por secciones
    initSectionNavigation();
    
    // Agregar indicadores de progreso
    initProgressIndicators();
}

// Mejoras para la subida de archivos
function initFileUploadEnhancements() {
    const fileInput = document.getElementById('inputDocumentos');
    const uploadArea = fileInput?.closest('.file-upload-area');

    if (!fileInput || !uploadArea) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.add('dragover');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.classList.remove('dragover');
        }, false);
    });

    uploadArea.addEventListener('drop', handleDrop, false);
    fileInput.addEventListener('change', handleFileSelect);

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    function handleDrop(e) {
        const dt = e.dataTransfer;
        addFiles(Array.from(dt.files));
    }

    function handleFileSelect() {
        addFiles(Array.from(fileInput.files));
    }

    function addFiles(newFiles) {
        const existingFileNames = uploadedFiles.map(file => file.name);
        newFiles.forEach(file => {
            if (!existingFileNames.includes(file.name)) {
                uploadedFiles.push(file);
            }
        });
        syncInputFiles();
        updateFilePreview();
    }

    function syncInputFiles() {
        const dt = new DataTransfer();
        uploadedFiles.forEach(file => dt.items.add(file));
        fileInput.files = dt.files;
    }

    function updateFilePreview() {
        const previewContainer = uploadArea.nextElementSibling || createPreviewContainer();
        previewContainer.innerHTML = '';

        uploadedFiles.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-preview-item';
            fileItem.innerHTML = `
                <span class="file-icon">📄</span>
                <span class="file-name">${file.name}</span>
                <span class="file-size">(${formatFileSize(file.size)})</span>
                <span class="remove-file" data-index="${index}">×</span>
            `;

            fileItem.querySelector('.remove-file').addEventListener('click', () => {
                removeFile(index);
            });

            previewContainer.appendChild(fileItem);
        });
    }

    function createPreviewContainer() {
        const container = document.createElement('div');
        container.className = 'file-preview';
        uploadArea.parentNode.insertBefore(container, uploadArea.nextSibling);
        return container;
    }

    function removeFile(index) {
        uploadedFiles.splice(index, 1);
        syncInputFiles();
        updateFilePreview();
    }

    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Validación de formulario en tiempo real
function initFormValidation() {
    const form = document.getElementById('formProyecto');
    if (!form) return;
    
    const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    requiredFields.forEach(field => {
        const fieldContainer = field.closest('.form-field');
        
        field.addEventListener('blur', () => {
            validateField(field, fieldContainer);
        });
        
        field.addEventListener('input', () => {
            if (fieldContainer.classList.contains('error')) {
                validateField(field, fieldContainer);
            }
        });
    });
    
    function validateField(field, container) {
        const isValid = field.checkValidity() && field.value.trim() !== '';
        
        container.classList.remove('error', 'success');
        
        if (!isValid) {
            container.classList.add('error');
        } else {
            container.classList.add('success');
        }
        
        return isValid;
    }
    
    // Validación al enviar el formulario
    form.addEventListener('submit', (e) => {
        let isFormValid = true;
        
        requiredFields.forEach(field => {
            const fieldContainer = field.closest('.form-field');
            const isFieldValid = validateField(field, fieldContainer);
            if (!isFieldValid) isFormValid = false;
        });
        
        if (!isFormValid) {
            e.preventDefault();
            showNotification('Por favor, complete todos los campos requeridos', 'error');
            
            // Scroll al primer campo con error
            const firstError = form.querySelector('.form-field.error');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
    });
}

// Navegación por secciones del formulario
function initSectionNavigation() {
    const sections = document.querySelectorAll('.form-section');
    
    sections.forEach((section, index) => {
        const title = section.querySelector('.section-title');
        if (!title) return;
        
        title.style.cursor = 'pointer';
        title.addEventListener('click', () => {
            // Scroll suave a la sección
            section.scrollIntoView({ behavior: 'smooth', block: 'start' });
            
            // Efecto visual temporal
            section.style.transform = 'scale(1.02)';
            setTimeout(() => {
                section.style.transform = '';
            }, 200);
        });
    });
}

// Indicadores de progreso del formulario
function initProgressIndicators() {
    const form = document.getElementById('formProyecto');
    const sections = document.querySelectorAll('.form-section');
    
    if (!form || sections.length === 0) return;
    
    // Crear barra de progreso
    const progressContainer = document.createElement('div');
    progressContainer.className = 'form-progress';
    progressContainer.innerHTML = `
        <div class="progress-bar">
            <div class="progress-fill" style="width: 0%"></div>
        </div>
    `;
    
    const formContent = form.querySelector('.form-sections');
    if (formContent) {
        formContent.insertBefore(progressContainer, formContent.firstChild);
    }
    
    const progressFill = progressContainer.querySelector('.progress-fill');
    
    // Actualizar progreso cuando se completan campos
    function updateProgress() {
        const requiredFields = form.querySelectorAll('input[required], select[required], textarea[required]');
        const completedFields = Array.from(requiredFields).filter(field => 
            field.value.trim() !== '' && field.checkValidity()
        );
        
        const progress = (completedFields.length / requiredFields.length) * 100;
        progressFill.style.width = `${progress}%`;
        
        // Cambiar color según el progreso
        if (progress < 30) {
            progressFill.style.background = 'linear-gradient(90deg, #f56565, #fc8181)';
        } else if (progress < 70) {
            progressFill.style.background = 'linear-gradient(90deg, #ed8936, #f6ad55)';
        } else {
            progressFill.style.background = 'linear-gradient(90deg, #0275d8, #1e88e5)';
        }
    }
    
    // Escuchar cambios en todos los campos
    form.addEventListener('input', updateProgress);
    form.addEventListener('change', updateProgress);
    
    // Actualizar progreso inicial
    updateProgress();
}

// Función para mostrar notificaciones
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 16px 24px;
        background: ${type === 'error' ? '#fed7d7' : type === 'success' ? '#c6f6d5' : '#bee3f8'};
        color: ${type === 'error' ? '#c53030' : type === 'success' ? '#2f855a' : '#2c5282'};
        border: 1px solid ${type === 'error' ? '#feb2b2' : type === 'success' ? '#9ae6b4' : '#90cdf4'};
        border-radius: 8px;
        font-weight: 500;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10000;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
    `;
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Auto-eliminar después de 5 segundos
    setTimeout(() => {
        notification.style.animation = 'slideOutRight 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Inicializar todas las mejoras cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', () => {
    // Pequeño delay para asegurar que todos los elementos estén renderizados
    setTimeout(initModernModalEnhancements, 100);
});

// Verificar si venimos del modal de documentos
if (sessionStorage.getItem('from_documents') === '1') {
    const licitacionId = sessionStorage.getItem('open_documents_for_licitacion');
    if (licitacionId) {
        // Limpiar el sessionStorage
        sessionStorage.removeItem('from_documents');
        sessionStorage.removeItem('open_documents_for_licitacion');
        
        // Abrir el modal de documentos para la licitación específica
        setTimeout(() => {
            // Buscar el botón de documentos para esa licitación
            document.querySelectorAll('.documentos-fila').forEach(btn => {
                if (btn.getAttribute('data-id') === licitacionId) {
                    btn.click();
                }
            });
        }, 300);
    }
}

window.addEventListener('resize', function() {
    // Ajustar el modal de documentos al tamaño de la ventana
    const modalDocumentos = document.getElementById('modalDocumentos');
    if (modalDocumentos.style.display === 'flex') {
        gestionarOverflowBody();
    }
});

// ===== MODAL DE CRONOLOGÍA =====
function setupModalCronologia() {
    const modalCronologia = document.getElementById('modalCronologia');
    const cerrarModalCronologia = document.getElementById('cerrarModalCronologia');
    const lineaTiempoContainer = document.getElementById('lineaTiempoContainer');
    
    if (!modalCronologia || !lineaTiempoContainer) return;
    
    // Configurar botones de cronología
    document.querySelectorAll('.cronologia-fila').forEach(btn => {
        btn.addEventListener('click', async function(e) {
            e.stopPropagation();
            const licitacionId = this.getAttribute('data-id');
            await abrirModalCronologia(licitacionId);
        });
    });
    
    // Cerrar modal
    if (cerrarModalCronologia) {
        cerrarModalCronologia.addEventListener('click', function() {
            cerrarModal(modalCronologia);
        });
    }
    
    // Cerrar modal al hacer click fuera
    modalCronologia.addEventListener('click', function(event) {
        if (event.target === modalCronologia) {
            cerrarModal(modalCronologia);
        }
    });
}

async function abrirModalCronologia(licitacionId) {
    const modalCronologia = document.getElementById('modalCronologia');
    const lineaTiempoContainer = document.getElementById('lineaTiempoContainer');
    const tipoLicitacionDiv = document.getElementById('tipoLicitacionCronologia');
    const nombreEtapaDiv = document.getElementById('nombreEtapaActual');
    
    try {
        // Mostrar modal con loading
        modalCronologia.classList.add('active');
        lineaTiempoContainer.innerHTML = '<div class="loading-cronologia">Cargando cronología...</div>';
        
        // Obtener datos de la licitación
        const fila = document.querySelector(`.cronologia-fila[data-id='${licitacionId}']`)?.closest('tr');
        let tipoLicitacionNombre = '';
        
        if (fila) {
            const tipoCell = fila.querySelector('[data-campo="tipo_licitacion"]');
            if (tipoCell) {
                tipoLicitacionNombre = tipoCell.innerText.trim();
            }
        }
        
        // Si no encontramos el tipo por la fila, buscar directamente en la tabla
        if (!tipoLicitacionNombre) {
            // Buscar en todas las filas de la tabla por el ID de licitación
            const todasLasFilas = document.querySelectorAll('.tabla-proyectos tbody tr');
            for (const filaTabla of todasLasFilas) {
                // Verificar si el atributo data-id del <tr> coincide con el licitacionId
                if (String(filaTabla.getAttribute('data-id')) === String(licitacionId)) {
                    const tipoCell = filaTabla.querySelector('[data-campo="tipo_licitacion"]');
                    if (tipoCell) {
                        tipoLicitacionNombre = tipoCell.innerText.trim();
                        break;
                    }
                }
            }
        }
        
        // Como último recurso, obtener el tipo de licitación desde la API
        if (!tipoLicitacionNombre) {
            try {
                const resLicitacion = await fetch(`/api/licitacion/${licitacionId}/`);
                if (resLicitacion.ok) {
                    const dataLicitacion = await resLicitacion.json();
                    console.log(dataLicitacion); // Debug
                    if (dataLicitacion.tipo_licitacion && dataLicitacion.tipo_licitacion.nombre) {
                        tipoLicitacionNombre = dataLicitacion.tipo_licitacion.nombre;
                    }
                }
            } catch (err) {
                console.error('Error al obtener datos de licitación desde API:', err);
            }
        }
        
        // Mostrar tipo de licitación con debug
        console.log(`Debug: Tipo de licitación encontrado: "${tipoLicitacionNombre}"`);
        if (tipoLicitacionDiv) {
            tipoLicitacionDiv.textContent = tipoLicitacionNombre || 'No especificado';
        }
        
        // Obtener etapa actual y etapas con información de inhabilitación
        let etapaActualId = '';
        let etapasLicitacion = [];
        
        try {
            // Obtener etapa actual
            const resEtapa = await fetch(`/api/licitacion/${licitacionId}/etapa/`);
            if (resEtapa.ok) {
                const dataEtapa = await resEtapa.json();
                etapaActualId = dataEtapa.etapa_id;
            }
            
            // Obtener etapas con información de inhabilitación
            const resEtapas = await fetch(`/api/licitacion/${licitacionId}/etapas/`);
            if (resEtapas.ok) {
                const dataEtapas = await resEtapas.json();
                etapasLicitacion = dataEtapas.etapas || [];
                
                // Mostrar información adicional si se detecta que debe saltar etapa
                if (dataEtapas.debe_saltar_etapas) {
                    console.log(`Licitación ${licitacionId}: Saltando etapas saltadas (${dataEtapas.moneda}: ${dataEtapas.monto})`);
                }
            }
        } catch (err) {
            console.error('Error al obtener etapas:', err);
            // Fallback al método anterior con datos globales
            console.log(`Debug fallback: Buscando tipo "${tipoLicitacionNombre}" en datos globales`);
            console.log('Tipos disponibles:', window.tiposLicitacion);
            
            const tipoObj = (window.tiposLicitacion || []).find(t => t.nombre === tipoLicitacionNombre);
            console.log('Tipo encontrado:', tipoObj);
            
            if (tipoObj && window.tiposLicitacionEtapaRaw && window.etapasLicitacion) {
                const ids = (window.tiposLicitacionEtapaRaw[tipoObj.id] || []);
                console.log(`Etapas para tipo ${tipoObj.id}:`, ids);
                
                if (ids.length) {
                    etapasLicitacion = ids.map(id => {
                        const etapa = window.etapasLicitacion.find(e => String(e.id) === String(id));
                        return etapa ? {...etapa, inhabilitada: false} : null;
                    }).filter(Boolean);
                    console.log('Etapas mapeadas:', etapasLicitacion);
                }
            } else {
                console.log('No se pudo usar fallback - datos faltantes o tipo no encontrado');
            }
        }
        
        // Renderizar timeline con información de inhabilitación
        renderizarTimeline(lineaTiempoContainer, etapasLicitacion, etapaActualId);
        
        // Mostrar etapa actual
        const etapaActual = etapasLicitacion.find(e => String(e.id) === String(etapaActualId));
        if (nombreEtapaDiv) {
            nombreEtapaDiv.textContent = etapaActual ? etapaActual.nombre : 'No definida';
            nombreEtapaDiv.dataset.etapaId = etapaActualId;
            nombreEtapaDiv.dataset.licitacionId = licitacionId;
        }
        
        // Configurar botones de avanzar/retroceder (SOLO con etapas habilitadas)
        const etapasHabilitadas = etapasLicitacion.filter(e => !e.inhabilitada);
        configurarBotonesCronologia(licitacionId, etapasHabilitadas, etapaActualId);
        
    } catch (error) {
        console.error('Error al abrir modal de cronología:', error);
        mostrarNotificacion('Error al cargar la cronología', 'error');
        cerrarModal(modalCronologia);
    }
}

function renderizarTimeline(container, etapas, etapaActualId) {
    if (!container || !etapas.length) {
        container.innerHTML = '<p style="text-align: center; color: #64748b;">No se encontraron etapas para esta licitación.</p>';
        return;
    }
    
    const lista = document.createElement('ul');
    lista.style.listStyle = 'none';
    lista.style.padding = '0';
    lista.style.margin = '0';
    
    // Encontrar el índice de la etapa actual (solo entre etapas habilitadas)
    const etapasHabilitadas = etapas.filter(e => !e.inhabilitada);
    const etapaActualIndex = etapasHabilitadas.findIndex(e => String(e.id) === String(etapaActualId));
    
    etapas.forEach((etapa, idx) => {
        const item = document.createElement('li');
        item.style.display = 'flex';
        item.style.alignItems = 'center';
        item.style.margin = '20px 0';
        item.style.position = 'relative';
        
        const icono = document.createElement('span');
        icono.className = 'etapa-icono';
        
        const nombre = document.createElement('span');
        nombre.className = 'etapa-nombre';
        nombre.textContent = etapa.nombre;
        
        // Determinar estado de la etapa
        if (etapa.inhabilitada) {
            // Etapa inhabilitada
            icono.classList.add('inhabilitada');
            nombre.classList.add('inhabilitada');
            icono.textContent = '✖';
            icono.style.color = '#9ca3af';
            icono.style.backgroundColor = '#f3f4f6';
            nombre.style.color = '#9ca3af';
            nombre.style.textDecoration = 'line-through';
        } else {
            // Calcular el índice de esta etapa dentro de las habilitadas
            const idxEnHabilitadas = etapasHabilitadas.findIndex(e => String(e.id) === String(etapa.id));
            
            if (String(etapa.id) === String(etapaActualId)) {
                icono.classList.add('actual');
                nombre.classList.add('actual');
                icono.textContent = '★';
            } else if (idxEnHabilitadas !== -1 && idxEnHabilitadas < etapaActualIndex) {
                icono.classList.add('completada');
                nombre.classList.add('completada');
                icono.textContent = '✓';
            } else {
                icono.classList.add('pendiente');
                icono.textContent = '○';
            }
        }
        
        item.appendChild(icono);
        item.appendChild(nombre);
        
        // Agregar tooltip para etapas inhabilitadas
        if (etapa.inhabilitada) {
            item.title = 'Etapa inhabilitada: Moneda UF con monto menor a 500';
            item.style.cursor = 'help';
        }
        
        lista.appendChild(item);
    });
    
    container.innerHTML = '';
    container.appendChild(lista);
    
    // Scroll automático a la etapa actual
    setTimeout(() => {
        const etapaActualElement = lista.querySelector('.etapa-icono.actual');
        if (etapaActualElement) {
            etapaActualElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 300);
}

function configurarBotonesCronologia(licitacionId, etapas, etapaActualId) {
    const btnRetroceder = document.getElementById('retrocederEtapa');
    const btnAvanzar = document.getElementById('avanzarEtapa');
    
    if (!btnRetroceder || !btnAvanzar) return;
    
    const etapaActualIndex = etapas.findIndex(e => String(e.id) === String(etapaActualId));
    
    // Limpiar listeners previos
    btnRetroceder.replaceWith(btnRetroceder.cloneNode(true));
    btnAvanzar.replaceWith(btnAvanzar.cloneNode(true));
    
    // Re-obtener referencias
    const btnRetrocederNew = document.getElementById('retrocederEtapa');
    const btnAvanzarNew = document.getElementById('avanzarEtapa');
    
    // Habilitar/deshabilitar botones
    btnRetrocederNew.disabled = etapaActualIndex <= 0;
    btnAvanzarNew.disabled = etapaActualIndex >= etapas.length - 1 || etapaActualIndex === -1;
    
    // Configurar listeners
    btnRetrocederNew.addEventListener('click', async function() {
        if (etapaActualIndex > 0) {
            const nuevaEtapaId = etapas[etapaActualIndex - 1].id;
            await cambiarEtapa(licitacionId, nuevaEtapaId, 'retroceder');
        }
    });
    
    btnAvanzarNew.addEventListener('click', async function() {
        if (etapaActualIndex < etapas.length - 1 && etapaActualIndex !== -1) {
            const nuevaEtapaId = etapas[etapaActualIndex + 1].id;
            await cambiarEtapa(licitacionId, nuevaEtapaId, 'avanzar');
        }
    });
}

async function cambiarEtapa(licitacionId, nuevaEtapaId, accion) {
    if (!licitacionId || !nuevaEtapaId) return false;
    
    try {
        const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const res = await fetch(`/api/licitacion/${licitacionId}/actualizar_etapa/`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json', 
                'X-CSRFToken': csrftoken 
            },
            body: JSON.stringify({ 
                etapa_id: nuevaEtapaId, 
                accion: accion,
                crear_entrada_bitacora: true  // Indicar que se debe crear entrada automática
            })
        });
        
        const data = await res.json();
        
        if (res.ok && data.ok) {
            mostrarNotificacion(`Etapa actualizada a: ${data.etapa.nombre}`, 'success');
            
            // Mostrar mensaje adicional si se creó entrada en bitácora
            if (data.entrada_bitacora_creada) {
                setTimeout(() => {
                    mostrarNotificacion('Entrada automática creada en la bitácora', 'info');
                }, 1500);
            }
            
            // Mostrar mensaje si hubo cambio de operador activo
            if (data.operador_activo && data.operador_activo.numero) {
                const numeroOperador = data.operador_activo.numero;
                const nombreOperador = data.operador_activo.nombre || data.operador_activo.username;
                
                if (numeroOperador === 2) {
                    setTimeout(() => {
                        mostrarNotificacion(`Licitación transferida automáticamente al Operador 2: ${nombreOperador}`, 'info');
                    }, 2000);
                }
            }
            
            // Actualizar la tabla principal
            const fila = document.querySelector(`.cronologia-fila[data-id='${licitacionId}']`)?.closest('tr');
            if (fila) {
                const etapaCell = fila.querySelector('[data-campo="etapa"]');
                if (etapaCell) etapaCell.textContent = data.etapa.nombre;
                
                // Actualizar los badges de operadores si hubo cambio
                if (data.operador_activo) {
                    const operadoresCell = fila.querySelector('[data-campo="operadores"]');
                    if (operadoresCell) {
                        // Actualizar los badges para reflejar el operador activo
                        const badges = operadoresCell.querySelectorAll('.operador-badge');
                        badges.forEach(badge => {
                            badge.classList.remove('activo');
                            const operadorNum = badge.classList.contains('operador-1') ? 1 : 2;
                            if (operadorNum === data.operador_activo.numero) {
                                badge.classList.add('activo');
                            }
                        });
                    }
                }
            }
            
            // Recargar la cronología para reflejar el cambio
            setTimeout(() => {
                abrirModalCronologia(licitacionId);
            }, 500);
            
            return true;
        } else {
            mostrarNotificacion(data.error || 'Error al actualizar etapa', 'error');
            return false;
        }
    } catch (e) {
        console.error('Error al cambiar etapa:', e);
        mostrarNotificacion('Error de conexión al actualizar etapa', 'error');
        return false;
    }
}

function cerrarModal(modal) {
    modal.classList.remove('active');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Inicializar modal de cronología cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(setupModalCronologia, 100);
});

// Manejar cambios de tamaño de la ventana para ajustar el modal de fallidas
window.addEventListener('resize', function() {
    if (modalLicitacionesFallidas && modalLicitacionesFallidas.classList.contains('active')) {
        const modalPrincipal = document.getElementById('modalProyecto');
        const modalContent = modalPrincipal?.querySelector('.modal-content');
        
        if (modalContent) {
            // Ajustar el ancho del modal de fallidas al del modal principal
            modalLicitacionesFallidas.style.width = `${modalContent.offsetWidth}px`;
        }
    }
});

// --- MODAL CERRAR LICITACIÓN (ADMIN) ---
document.addEventListener('DOMContentLoaded', function() {
    const modalCerrarLicitacion = document.getElementById('modalCerrarLicitacion');
    const cerrarModalCerrarLicitacion = document.getElementById('cerrarModalCerrarLicitacion');
    const btnCancelarCerrarLicitacion = document.getElementById('btnCancelarCerrarLicitacion');
    const formCerrarLicitacion = document.getElementById('formCerrarLicitacion');
    const licitacionFallidaCheckbox = document.getElementById('licitacionFallidaCheckbox');
    const tipoFallidaContainer = document.getElementById('tipoFallidaContainer');
    const tipoFallidaSelect = document.getElementById('tipoFallidaSelect');

    // Mostrar/ocultar select de tipo de falla según checkbox
    if (licitacionFallidaCheckbox && tipoFallidaContainer) {
        licitacionFallidaCheckbox.addEventListener('change', function() {
            if (this.checked) {
                tipoFallidaContainer.style.display = 'block';
            } else {
                tipoFallidaContainer.style.display = 'none';
                if (tipoFallidaSelect) {
                    tipoFallidaSelect.value = '';
                }
            }
        });
    }

    // Configurar botones de cerrar licitación
    document.querySelectorAll('.cerrar-licitacion-fila').forEach(btn => {
        btn.addEventListener('click', function() {
            // No permitir la acción si el botón está deshabilitado
            if (this.disabled) {
                return;
            }
            
            const licitacionId = this.getAttribute('data-id');
            document.getElementById('cerrarLicitacionId').value = licitacionId;
            document.getElementById('cerrarLicitacionTexto').value = '';
            document.getElementById('licitacionFallidaCheckbox').checked = false;
            
            // Resetear y ocultar el select de tipo de falla
            if (tipoFallidaContainer) {
                tipoFallidaContainer.style.display = 'none';
            }
            if (tipoFallidaSelect) {
                tipoFallidaSelect.value = '';
            }
            gestionarOverflowBody();
        });
    });

    // Configurar cierre del modal de cerrar licitación
    if (cerrarModalCerrarLicitacion) {
        cerrarModalCerrarLicitacion.onclick = function() { 
            modalCerrarLicitacion.style.display = 'none'; 
            gestionarOverflowBody();
        };
    }

    if (btnCancelarCerrarLicitacion) {
        btnCancelarCerrarLicitacion.onclick = function() { 
            modalCerrarLicitacion.style.display = 'none'; 
            gestionarOverflowBody();
        };
    }

    // Cerrar el modal al hacer clic fuera
    window.addEventListener('click', function(event) {
        if (event.target === modalCerrarLicitacion) {
            modalCerrarLicitacion.style.display = 'none';
            gestionarOverflowBody();
        }
    });

    // Funcionalidad para los checkboxes de tipo de monto (solo uno puede estar seleccionado)
    const montoMaximoCheck = document.getElementById('montoMaximoCheck');
    const montoReferencialCheck = document.getElementById('montoReferencialCheck');
    
    if (montoMaximoCheck && montoReferencialCheck) {
        montoMaximoCheck.addEventListener('change', function() {
            if (this.checked) {
                montoReferencialCheck.checked = false;
            }
        });
        
        montoReferencialCheck.addEventListener('change', function() {
            if (this.checked) {
                montoMaximoCheck.checked = false;
            }
        });
    }
});
document.addEventListener('DOMContentLoaded', function() {
    
    const btnAgregar = document.getElementById('btnNuevoDepartamento');
    const selectDept = document.getElementById('departamentoInput');

    // Solo funciona si el botón existe en la pantalla
    if (btnAgregar && selectDept) {

        btnAgregar.addEventListener('click', function() {
            // 1. Pedir el nombre al usuario con una ventanita simple del navegador
            let nuevoNombre = prompt("Escriba el nombre del nuevo departamento:");

            // Si el usuario escribió algo y no le dio Cancelar
            if (nuevoNombre && nuevoNombre.trim() !== "") {
                
                // Obtener la URL y el Token de seguridad
                const url = selectDept.getAttribute('data-url');
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

                // 2. Enviar a Django
                fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ nombre: nuevoNombre })
                })
                .then(response => response.json())
                .then(result => {
                    if (result.id) {
                        // ÉXITO: Crear la nueva opción en HTML
                        const nuevaOpcion = document.createElement('option');
                        nuevaOpcion.value = result.id;
                        nuevaOpcion.text = result.nombre;
                        nuevaOpcion.selected = true; // Lo seleccionamos automáticamente

                        // Agregarla a la lista
                        selectDept.appendChild(nuevaOpcion);
                        
                        alert("Departamento '" + result.nombre + "' agregado correctamente.");
                    } else {
                        alert("Error: " + (result.error || "No se pudo guardar"));
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert("Error de conexión.");
                });
            }
        });
    }
});

function agregarFilaCuenta(valor = "") {
    const contenedor = document.getElementById('contenedorCuentas');
    if (!contenedor) return;

    const div = document.createElement('div');
    div.style.cssText = "display: flex; gap: 5px; align-items: center;";
    
    // El input visible
    const input = document.createElement('input');
    input.type = "text";
    input.className = "input-cuenta-visual"; // Clase para identificarlos
    input.value = valor;
    input.placeholder = "Ingrese N° cuenta";
    input.style.flex = "1"; // Que ocupe el espacio
    
    // Si es el primer input, lo hacemos obligatorio
    if (contenedor.children.length === 0) {
        input.required = true;
    }

    // Botón para borrar (solo si no es el único)
    const btnBorrar = document.createElement('button');
    btnBorrar.type = "button";
    btnBorrar.innerHTML = "🗑️";
    btnBorrar.style.cssText = "border: none; background: #ffebee; cursor: pointer; padding: 5px; border-radius: 4px;";
    btnBorrar.onclick = function() {
        if (contenedor.children.length > 1) {
            div.remove();
            actualizarInputOcultoCuentas();
        } else {
            input.value = ""; // Si es el último, solo limpia
            actualizarInputOcultoCuentas();
        }
    };

    // Evento: cada vez que escriban, actualizamos el hidden
    input.addEventListener('input', actualizarInputOcultoCuentas);

    div.appendChild(input);
    div.appendChild(btnBorrar);
    contenedor.appendChild(div);
    
    actualizarInputOcultoCuentas(); // Actualizar al agregar
}

// 2. Función que une todos los valores en el input oculto (separados por " / ")
function actualizarInputOcultoCuentas() {
    const inputs = document.querySelectorAll('.input-cuenta-visual');
    const valores = [];
    
    inputs.forEach(inp => {
        if (inp.value.trim() !== "") {
            valores.push(inp.value.trim());
        }
    });

    // Unimos con " / " (ej: "11111 / 22222")
    const inputReal = document.getElementById('numeroCuentaReal');
    if (inputReal) {
        inputReal.value = valores.join(" / ");
    }
}

// 3. Inicializar el botón de agregar
document.addEventListener('DOMContentLoaded', function() {
    const btnAdd = document.getElementById('btnAgregarCuentaInput');
    if (btnAdd) {
        btnAdd.addEventListener('click', function() {
            agregarFilaCuenta("");
        });
    }
});


function gestionarVisibilidadFecha(esEdicion) {
    const inputCreacion = document.getElementById('fechaCreacionInput');
    
    if (!inputCreacion) return;

    // Buscamos el contenedor padre (div.form-group o col-md-*) para ocultar también el Label
    const contenedor = inputCreacion.closest('.form-group') || inputCreacion.closest('.col') || inputCreacion.parentElement;

    if (contenedor) {
        if (esEdicion) {
            // MODO EDICIÓN: Quitamos el display none (volvemos al default)
            contenedor.style.display = ''; 
            // Aseguramos que el input sea editable si así lo deseas
            inputCreacion.disabled = false; 
        } else {
            // MODO CREACIÓN: Ocultamos todo el bloque visualmente
            contenedor.style.display = 'none'; 
        }
    }
}



document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Capturamos tu botón de agregar
    const btnAgregar = document.getElementById('btnAgregarLicitacion');
    
    if (btnAgregar) {
        btnAgregar.addEventListener('click', function() {
            // A. Reseteamos el formulario para que esté limpio
            // Asegúrate que 'formProyecto' sea el ID de tu etiqueta <form>
            const form = document.getElementById('formProyecto'); 
            if (form) form.reset();

            // B. AQUÍ ESTÁ LA CLAVE: Forzamos modo "Creación" (False)
            // Esto llamará a la función que creamos antes para ocultar el div
            if (typeof gestionarVisibilidadFecha === "function") {
                gestionarVisibilidadFecha(false);
            }

            // C. Si no usas data-toggle en el HTML, abre el modal aquí:
            // $('#tuModalId').modal('show'); 
        });
    }
});

document.addEventListener('click', function(event) {
    // 1. Verificamos si el clic fue en un botón con la clase 'editar-fila'
    // (o en el ícono del lápiz que está dentro del botón)
    const btnEditar = event.target.closest('.editar-fila');

    if (btnEditar) {
        // ¡Detectamos clic en Editar!
        
        // 2. Ejecutamos la función para MOSTRAR la fecha
        // (True = Modo Edición = Visible)
        if (typeof gestionarVisibilidadFecha === 'function') {
            gestionarVisibilidadFecha(true);
        }
        
        // Opcional: Log para verificar en consola
        console.log("Editando: Campo fecha activado.");
    }
});
document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ DOMContentLoaded - info general JS cargado");

    const modalInfo = document.getElementById("modalInfoGeneral");
    const cerrarModalInfo = document.getElementById("cerrarModalInfo");
    const contenido = document.getElementById("contenidoInfoGeneral");

    console.log("🔍 modalInfo:", modalInfo);
    console.log("🔍 cerrarModalInfo:", cerrarModalInfo);
    console.log("🔍 contenido:", contenido);

    const botones = document.querySelectorAll(".info-general-fila");
    console.log("🔘 botones .info-general-fila encontrados:", botones.length);

    botones.forEach((btn, index) => {
        console.log(`➡️ Bind click botón ${index}`, btn);

        btn.addEventListener("click", (e) => {
            e.preventDefault();
            e.stopPropagation();

            console.log("🟢 CLICK info-general-fila");

            const licitacionId = btn.dataset.id;
            console.log("📌 data-id:", licitacionId);

            if (!licitacionId) {
                console.warn("⚠️ NO hay data-id en el botón");
                alert("Selecciona una licitación primero");
                return;
            }

            const fila = document.querySelector(`tr[data-id="${licitacionId}"]`);
            console.log("📄 fila encontrada:", fila);

            if (!fila) {
                console.error("❌ No se encontró la fila con data-id", licitacionId);
                alert("No se encontró la fila de la licitación");
                return;
            }

            const get = campo => {
                const celda = fila.querySelector(`[data-campo="${campo}"]`);
                console.log(`🔎 campo "${campo}" →`, celda?.innerText);
                return celda?.innerText.trim() || "-";
            };

            console.log("🧩 Construyendo contenido del modal");

            contenido.innerHTML = `
                <div class="info-grid">
                    <div><strong>Iniciativa</strong><br>${get("iniciativa")}</div>
                    <div><strong>N° Pedido</strong><br>${get("numero_pedido")}</div>
                    <div><strong>Departamento</strong><br>${get("departamento")}</div>
                    <div><strong>Profesionales</strong><br>${get("operadores")}</div>
                    <div><strong>Estado</strong><br>${get("estado")}</div>
                    <div><strong>Etapa</strong><br>${get("etapa")}</div>
                    <div><strong>Tipo Licitación</strong><br>${get("tipo_licitacion")}</div>
                    <div><strong>Monto</strong><br>${get("monto_presupuestado")}</div>
                </div>
            `;

            console.log("📢 Abriendo modal");
            modalInfo.classList.add("active");
            modalInfo.style.display = "flex";
            modalInfo.style.zIndex = "9999";
            gestionarOverflowBody();
        });
    });

    if (cerrarModalInfo) {
        cerrarModalInfo.addEventListener("click", () => {
            console.log("❎ Cerrar modal info general");
            modalInfo.classList.remove("active");
            modalInfo.style.display = "none";
            gestionarOverflowBody();
        });
    } else {
        console.warn("⚠️ cerrarModalInfo no encontrado");
    }
});

