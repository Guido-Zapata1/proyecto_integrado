document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // 1. CONFIGURACIÓN DEL CALENDARIO (CONECTADO A BD)
    // ==========================================
    var calendarEl = document.getElementById('calendar');
    
    if (calendarEl) {
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'timeGridWeek',
            locale: 'es',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek'
            },
            // Horario laboral (visual)
            businessHours: {
                daysOfWeek: [1, 2, 3, 4, 5], // Lunes a Viernes
                startTime: '08:00',
                endTime: '20:00',
            },
            // Rango de horas visible
            slotMinTime: "08:00:00",
            slotMaxTime: "21:00:00",
            
            // --- AQUÍ ESTÁ LA MAGIA ---
            // Conectamos el calendario a la URL que creamos en Django
            events: '/reservas/api/reservas-calendario/',
            
            // Si falla la carga
            failure: function() {
                Swal.fire('Error', 'No se pudieron cargar los eventos del calendario.', 'error');
            },

            eventClick: function(info) {
                Swal.fire({
                    title: info.event.title,
                    text: 'Inicio: ' + info.event.start.toLocaleTimeString() + ' - Fin: ' + info.event.end.toLocaleTimeString(),
                    icon: 'info'
                });
            }
        });

        // FIX: Renderizar calendario correctamente cuando el modal se abre
        var calendarModal = document.getElementById('calendarModal');
        if (calendarModal) {
            calendarModal.addEventListener('shown.bs.modal', function () {
                calendar.render();
                calendar.updateSize(); // Forza el ajuste de tamaño
            });
        }
    }

    // ==========================================
    // 2. LÓGICA DE RECURSOS (CARRITO DE COMPRAS)
    // ==========================================
    
    window.recursosList = [];

    // A. DETECCIÓN AUTOMÁTICA (PARA EDITAR)
    const dataScript = document.getElementById('data-recursos');
    if (dataScript) {
        try {
            const datosCargados = JSON.parse(dataScript.textContent);
            if (Array.isArray(datosCargados) && datosCargados.length > 0) {
                window.recursosList = datosCargados;
                window.actualizarTabla();
            }
        } catch (e) {
            console.error("Error al leer datos JSON:", e);
        }
    }

    // B. BOTÓN AGREGAR (CON VALIDACIÓN DE STOCK EN TIEMPO REAL)
    const btnAgregar = document.getElementById('btnAgregarRecurso');
    if (btnAgregar) {
        btnAgregar.addEventListener('click', function() {
            const selector = document.getElementById('recurso_selector');
            const cantidadInput = document.getElementById('recurso_cantidad');
            const stockAlert = document.getElementById('stock-alert');
            
            // Datos del formulario para validar disponibilidad específica
            const idRecurso = selector.value;
            const fechaVal = document.getElementById('id_fecha')?.value;
            const horaIniVal = document.getElementById('id_hora_inicio')?.value;
            const horaFinVal = document.getElementById('id_hora_fin')?.value;

            if (!idRecurso) {
                Swal.fire('Atención', 'Seleccione un recurso.', 'warning');
                return;
            }
            
            if (!fechaVal || !horaIniVal || !horaFinVal) {
                Swal.fire('Faltan Datos', 'Primero selecciona fecha y horas para verificar el stock disponible en ese bloque.', 'info');
                return;
            }

            const cantidad = parseInt(cantidadInput.value);
            if (isNaN(cantidad) || cantidad <= 0) return;

            // Feedback visual de carga
            const btnText = btnAgregar.innerHTML;
            btnAgregar.disabled = true;
            btnAgregar.innerHTML = '<span class="spinner-border spinner-border-sm"></span>';

            // CONSULTA AL BACKEND
            const url = `/reservas/api/consultar-stock/?recurso_id=${idRecurso}&fecha=${fechaVal}&hora_inicio=${horaIniVal}&hora_fin=${horaFinVal}`;

            fetch(url)
                .then(res => res.json())
                .then(data => {
                    btnAgregar.disabled = false;
                    btnAgregar.innerHTML = btnText;

                    if (data.error) {
                        Swal.fire('Error', data.error, 'error');
                        return;
                    }

                    const stockReal = data.stock_real;
                    
                    // Verificar si ya agregué este recurso a mi lista local
                    const existente = window.recursosList.find(r => r.id === idRecurso);
                    const cantidadPrevia = existente ? existente.cantidad : 0;
                    
                    if ((cantidad + cantidadPrevia) > stockReal) {
                        stockAlert.innerHTML = `<strong>Stock insuficiente.</strong> Solo quedan ${stockReal} unidades disponibles en ese horario.`;
                        stockAlert.classList.remove('d-none');
                        return;
                    } else {
                        stockAlert.classList.add('d-none');
                    }

                    // Agregar
                    const nombreRecurso = selector.options[selector.selectedIndex].text.split('(')[0].trim();
                    
                    if (existente) {
                        existente.cantidad += cantidad;
                    } else {
                        window.recursosList.push({ id: idRecurso, nombre: nombreRecurso, cantidad: cantidad });
                    }

                    window.actualizarTabla();
                    selector.value = "";
                    cantidadInput.value = "";
                })
                .catch(err => {
                    console.error(err);
                    btnAgregar.disabled = false;
                    btnAgregar.innerHTML = btnText;
                });
        });
    }

    // C. FUNCIONES DE TABLA
    window.actualizarTabla = function() {
        const tbody = document.querySelector('#tabla_recursos tbody');
        const inputHidden = document.getElementById('recursos_input');
        
        if (tbody) {
            tbody.innerHTML = "";
            window.recursosList.forEach((r, i) => {
                tbody.innerHTML += `
                    <tr>
                        <td>${r.nombre}</td>
                        <td class="text-center">${r.cantidad}</td>
                        <td class="text-end">
                            <button type="button" class="btn btn-sm btn-outline-danger" onclick="window.eliminarRecurso(${i})">
                                <i class="bi bi-trash"></i>
                            </button>
                        </td>
                    </tr>`;
            });
        }
        if (inputHidden) {
            inputHidden.value = JSON.stringify(window.recursosList);
        }
    }

    window.eliminarRecurso = function(index) {
        window.recursosList.splice(index, 1);
        window.actualizarTabla();
    };

    // ==========================================
    // 3. VALIDACIÓN DE ARCHIVOS (Anti-Error OneDrive)
    // ==========================================
    const fileInput = document.getElementById('id_archivo_adjunto'); 

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            
            if (file) {
                if (file.size === 0) {
                    Swal.fire('Archivo no válido', 'El archivo está vacío o es un acceso directo de nube no descargado.', 'warning');
                    this.value = '';
                    return;
                }
                // Test de lectura
                const reader = new FileReader();
                reader.onerror = function() {
                    Swal.fire('Error de Lectura', 'No se puede leer el archivo. Asegúrese de que esté descargado en su PC (check verde) y no en la nube.', 'error');
                    fileInput.value = '';
                };
                reader.readAsArrayBuffer(file.slice(0, 1));
            }
        });
    }
});