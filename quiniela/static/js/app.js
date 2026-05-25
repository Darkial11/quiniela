// ================================
// SELECCIÓN DE PRONÓSTICOS
// ================================

const cards = document.querySelectorAll(".match-card");

cards.forEach((card) => {

    const opciones = card.querySelectorAll(".opcion");

    opciones.forEach((boton) => {

        boton.addEventListener("click", () => {

            opciones.forEach((btn) => {

                btn.classList.remove("seleccionado");

                btn.classList.add("apagado");

            });

            boton.classList.add("seleccionado");

            boton.classList.remove("apagado");

            setTimeout(() => actualizarContador(), 50);

        });

    });

});

// ================================
// CONTADOR DE SELECCIONES
// ================================

function actualizarContador() {

    const seleccionados = document.querySelectorAll(".seleccionado").length;

    const total = cards.length;

    const contador = document.getElementById("contador");

    if (contador) {

        contador.innerText = `${seleccionados}/${total}`;

    }

}

actualizarContador();

// ================================
// GUARDAR PRONÓSTICOS
// ================================

const btnGuardar = document.getElementById("guardar");

if (btnGuardar) {

    btnGuardar.addEventListener("click", () => {

        const pronosticos = [];

        cards.forEach((card) => {

            const partidoId = card.dataset.id;

            const seleccionado = card.querySelector(".seleccionado");

            if (seleccionado) {

                pronosticos.push({

                    partido_id: partidoId,

                    seleccion: seleccionado.innerText.trim()

                });

            }

        });

        if (pronosticos.length !== cards.length) {

            mostrarToast("Selecciona todos los partidos", "error");

            return;

        }

        // Estado: cargando
        btnGuardar.disabled = true;

        btnGuardar.classList.add("loading-btn");

        btnGuardar.innerHTML = `<span class="spinner"></span> Guardando...`;

        const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");

        if (!csrfToken) {

            mostrarToast("Error de seguridad, recarga la página", "error");

            resetearBoton();

            return;

        }

        fetch("/guardar/", {

            method: "POST",

            headers: {

                "Content-Type": "application/json",

                "X-CSRFToken": csrfToken.value

            },

            body: JSON.stringify({ pronosticos })

        })

        .then((response) => {

            if (!response.ok) {

                throw new Error(`Error del servidor: ${response.status}`);

            }

            return response.json();

        })

        .then((data) => {

            if (data.pago_requerido) {

                mostrarToast("Necesitas pagar para participar", "error");

                resetearBoton();

                return;

            }

            btnGuardar.innerHTML = "✓ Guardado";

            btnGuardar.classList.add("success-btn");

            mostrarToast(data.mensaje || "Pronósticos guardados", "success");

            setTimeout(() => resetearBoton(), 2500);

        })

        .catch((error) => {

            console.error("Error al guardar:", error);

            mostrarToast("Error de conexión, intenta de nuevo", "error");

            resetearBoton();

        });

    });

}

function resetearBoton() {

    if (!btnGuardar) return;

    btnGuardar.disabled = false;

    btnGuardar.classList.remove("loading-btn", "success-btn");

    btnGuardar.innerHTML = "Guardar Quiniela";

}

// ================================
// CARGAR PRONÓSTICOS GUARDADOS
// ================================

if (typeof window.jornadaActual !== "undefined") {

    fetch(`/cargar/${window.jornadaActual}/`)

    .then((response) => {

        if (!response.ok) {

            throw new Error(`Error cargando: ${response.status}`);

        }

        return response.json();

    })

    .then((data) => {

        data.forEach((item) => {

            const card = document.querySelector(`[data-id="${item.partido_id}"]`);

            if (!card) return;

            const botones = card.querySelectorAll(".opcion");

            botones.forEach((btn) => {

                if (btn.innerText.trim() === item.seleccion) {

                    btn.classList.add("seleccionado");

                } else {

                    btn.classList.add("apagado");

                }

            });

        });

        actualizarContador();

    })

    .catch((error) => {

        console.error("Error cargando pronósticos:", error);

    });

}

// ================================
// TOAST NOTIFICATIONS
// ================================

function mostrarToast(mensaje, tipo) {

    // Elimina toast anterior si existe
    const toastExistente = document.querySelector(".toast");

    if (toastExistente) toastExistente.remove();

    const toast = document.createElement("div");

    toast.className = `toast ${tipo}`;

    toast.innerText = mensaje;

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 50);

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => toast.remove(), 300);

    }, 2500);

}

// ================================
// BOTÓN PAGAR — GUARDA Y REDIRIGE
// ================================

const btnPagar = document.getElementById("btnPagar");

if (btnPagar) {

    btnPagar.addEventListener("click", () => {

        const pronosticos = [];

        cards.forEach((card) => {

            const partidoId = card.dataset.id;

            const seleccionado = card.querySelector(".seleccionado");

            if (seleccionado) {

                pronosticos.push({

                    partido_id: partidoId,

                    seleccion: seleccionado.innerText.trim()

                });

            }

        });

        const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]");

        if (!csrfToken) {

            mostrarToast("Error de seguridad, recarga la página", "error");

            return;

        }

        btnPagar.disabled = true;

        btnPagar.innerHTML = "⏳ Guardando...";

        fetch("/guardar/", {

            method: "POST",

            headers: {

                "Content-Type": "application/json",

                "X-CSRFToken": csrfToken.value

            },

            body: JSON.stringify({ pronosticos })

        })

        .then((response) => response.json())

        .then(() => {

            window.location.href = "/pagar/";

        })

        .catch(() => {

            window.location.href = "/pagar/";

        });

    });

}
