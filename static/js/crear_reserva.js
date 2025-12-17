document.addEventListener('DOMContentLoaded', function () {
  console.log("Reservas: JS cargado ✅");

  // ============================
  // Helpers DOM
  // ============================
  const $ = (id) => document.getElementById(id);

  // APIs desde template (evita hardcode)
  const API_CALENDARIO = window.API_CALENDARIO || '/reservas/api/reservas-calendario/';
  const API_STOCK = window.API_STOCK || '/reservas/api/consultar-stock/';

  // Si estamos editando, el template puede setear esto:
  const RESERVA_ID = window.RESERVA_ID || null;

  // ============================
  // 1) CALENDARIO (FullCalendar)
  // ============================
  const calendarEl = $('calendar');
  let calendarInstance = null;

  if (calendarEl && window.FullCalendar) {
    calendarInstance = new FullCalendar.Calendar(calendarEl, {
      initialView: 'timeGridWeek',
      locale: 'es',
      headerToolbar: {
        left: 'prev,next today',
        center: 'title',
        right: 'dayGridMonth,timeGridWeek'
      },
      businessHours: {
        daysOfWeek: [1, 2, 3, 4, 5],
        startTime: '08:00',
        endTime: '22:00',
      },
      slotMinTime: "08:00:00",
      slotMaxTime: "22:00:00",
      height: 'auto',
      events: API_CALENDARIO,
      eventClick: function (info) {
        if (window.Swal) {
          Swal.fire({
            title: 'Ocupado',
            text:
              info.event.title + " | " +
              info.event.start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) +
              " - " +
              info.event.end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            icon: 'warning',
            confirmButtonColor: '#D71920'
          });
        }
      }
    });

    // Render SOLO cuando el modal está visible
    const calendarModal = $('calendarModal');
    if (calendarModal) {
      calendarModal.addEventListener('shown.bs.modal', function () {
        calendarInstance.render();
        calendarInstance.updateSize();
      });
    }
  } else {
    console.warn("Calendario: no se encontró #calendar o FullCalendar no cargó.");
  }

  // ============================
  // 2) Selección visual de espacio
  // ============================
  const selectEspacio = $('id_espacio');
  if (selectEspacio) selectEspacio.classList.add('visually-hidden-select');

  window.selectSpace = function (id, cardElement) {
    if (selectEspacio) {
      selectEspacio.value = id;
      selectEspacio.dispatchEvent(new Event('change'));
    }
    document.querySelectorAll('.space-card').forEach(c => c.classList.remove('selected'));
    if (cardElement) cardElement.classList.add('selected');
  };

  // ============================
  // 3) Recursos/Stock (carrito)
  // ============================
  window.recursosList = [];

  // Cargar recursos preexistentes si el template los dejó
  const dataScript = $('data-recursos');
  if (dataScript) {
    try {
      const datos = JSON.parse(dataScript.textContent);
      if (Array.isArray(datos)) {
        window.recursosList = datos;
        actualizarTablaVisual();
      }
    } catch (e) {
      console.error("Error leyendo data-recursos:", e);
    }
  }

  const btnAgregar = $('btnAgregarRecurso');
  const stockAlert = $('stock-alert');

  if (btnAgregar) {
    btnAgregar.addEventListener('click', async function () {
      const selector = $('recurso_selector');
      const cantidadInput = $('recurso_cantidad');

      const idRecurso = selector?.value;
      const cantidad = parseInt(cantidadInput?.value);

      const fecha = $('id_fecha')?.value;
      const horaIni = $('id_hora_inicio')?.value;
      const horaFin = $('id_hora_fin')?.value;

      if (!idRecurso) {
        window.Swal ? Swal.fire('Falta info', 'Seleccione un recurso.', 'warning') : alert("Seleccione un recurso.");
        return;
      }
      if (!fecha || !horaIni || !horaFin) {
        window.Swal ? Swal.fire('Horario requerido', 'Seleccione fecha y horas primero.', 'info') : alert("Seleccione fecha y horas primero.");
        return;
      }
      if (isNaN(cantidad) || cantidad <= 0) {
        window.Swal ? Swal.fire('Cantidad inválida', 'Ingrese una cantidad mayor a 0.', 'warning') : alert("Cantidad inválida.");
        return;
      }

      // UI loading
      const btnText = btnAgregar.innerHTML;
      btnAgregar.disabled = true;
      btnAgregar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Verificando...';
      if (stockAlert) stockAlert.classList.add('d-none');

      try {
        const params = new URLSearchParams({
          recurso_id: idRecurso,
          fecha: fecha,
          hora_inicio: horaIni,
          hora_fin: horaFin
        });

        // Si estamos editando, mandamos reserva_id para que backend pueda excluirla si corresponde
        if (RESERVA_ID) params.append('reserva_id', RESERVA_ID);

        const url = `${API_STOCK}?${params.toString()}`;

        const res = await fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } });
        if (!res.ok) throw new Error("API stock error");
        const data = await res.json();

        if (data.error) {
          window.Swal ? Swal.fire('Error', data.error, 'error') : alert(data.error);
          return;
        }

        const stockReal = parseInt(data.stock_real);

        // Cantidad que ya está en carrito
        const existente = window.recursosList.find(r => r.id === idRecurso);
        const cantidadEnCarrito = existente ? existente.cantidad : 0;
        const total = cantidad + cantidadEnCarrito;

        if (total > stockReal) {
          if (stockAlert) {
            stockAlert.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> <strong>Stock insuficiente.</strong> Disponible: ${stockReal}. (Ya tienes ${cantidadEnCarrito})`;
            stockAlert.classList.remove('d-none');
          }
          return;
        }

        // Agregar / acumular
        const nombreRecurso = selector.options[selector.selectedIndex].text.split('(')[0].trim();

        if (existente) {
          existente.cantidad += cantidad;
        } else {
          window.recursosList.push({ id: idRecurso, nombre: nombreRecurso, cantidad });
        }

        actualizarTablaVisual();
        selector.value = "";
        cantidadInput.value = "";

      } catch (err) {
        console.error(err);
        window.Swal ? Swal.fire('Error', 'No se pudo verificar el stock.', 'error') : alert("No se pudo verificar stock.");
      } finally {
        btnAgregar.disabled = false;
        btnAgregar.innerHTML = btnText;
      }
    });
  }

  function actualizarTablaVisual() {
    const tbody = document.querySelector('#tabla_recursos tbody');
    const inputHidden = $('recursos_input');

    if (tbody) {
      tbody.innerHTML = "";
      window.recursosList.forEach((r, i) => {
        tbody.innerHTML += `
          <tr>
            <td>${r.nombre}</td>
            <td class="text-center">${r.cantidad}</td>
            <td class="text-end">
              <button type="button" class="btn btn-sm btn-outline-danger" onclick="eliminarRecurso(${i})">
                <i class="bi bi-trash"></i>
              </button>
            </td>
          </tr>
        `;
      });
    }

    if (inputHidden) {
      inputHidden.value = JSON.stringify(window.recursosList);
    }
  }

  window.eliminarRecurso = function (index) {
    window.recursosList.splice(index, 1);
    actualizarTablaVisual();
  };

  // ============================
  // 4) Validaciones visuales (horas)
  // ============================
  const horaInicio = $('id_hora_inicio');
  const horaFin = $('id_hora_fin');
  const timeError = $('time-error');

  function validarHoras() {
    if (horaInicio?.value && horaFin?.value) {
      if (horaFin.value <= horaInicio.value) {
        if (timeError) {
          timeError.innerText = "La hora de término debe ser posterior a la de inicio.";
          timeError.classList.remove('d-none');
        }
      } else {
        if (timeError) timeError.classList.add('d-none');
      }
    }
  }

  if (horaInicio && horaFin) {
    horaInicio.addEventListener('change', validarHoras);
    horaFin.addEventListener('change', validarHoras);
  }
});
