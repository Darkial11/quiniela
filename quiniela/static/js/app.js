const cards = document.querySelectorAll(

    ".match-card"

);

cards.forEach((card) => {

    const opciones = card.querySelectorAll(

        ".opcion"

    );

    opciones.forEach((boton) => {

        boton.addEventListener("click", () => {

            opciones.forEach((btn) => {

                btn.classList.remove(

                    "seleccionado"

                );

                btn.classList.add(

                    "apagado"

                );

            });

            boton.classList.add(

                "seleccionado"

            );

            boton.classList.remove(

                "apagado"

            );

        });

    });

});

const btnGuardar = document.getElementById(

    "guardar"

);

btnGuardar.addEventListener("click", () => {

    let pronosticos = [];

    cards.forEach((card) => {

        const partidoId = card.dataset.id;

        const seleccionado = card.querySelector(

            ".seleccionado"

        );

        if(seleccionado){

            pronosticos.push({

                partido_id: partidoId,

                seleccion: seleccionado.innerText

            });

        }

    });

    if(pronosticos.length !== cards.length){

        mostrarToast(

            "Selecciona todos los partidos",

            "error"

        );

        return;

    }

    btnGuardar.disabled = true;

    btnGuardar.classList.add(

        "loading-btn"

    );

    btnGuardar.innerHTML = `

        <span class="spinner"></span>

        Guardando...

    `;

    fetch("/guardar/", {

        method: "POST",

        headers: {

            "Content-Type": "application/json",

            "X-CSRFToken": document.querySelector(

                '[name=csrfmiddlewaretoken]'

            ).value

        },

        body: JSON.stringify({

            pronosticos: pronosticos

        })

    })

    .then(response => response.json())

    .then(data => {

        btnGuardar.innerHTML =

            "✓ Guardado";

        btnGuardar.classList.add(

            "success-btn"

        );

        mostrarToast(

            data.mensaje,

            "success"

        );

        setTimeout(() => {

            btnGuardar.disabled = false;

            btnGuardar.classList.remove(

                "loading-btn"

            );

            btnGuardar.classList.remove(

                "success-btn"

            );

            btnGuardar.innerHTML =

                "Guardar Quiniela";

        }, 2000);

    });

});

fetch(

    `/cargar/${window.jornadaActual}/`

)

.then(response => response.json())

.then(data => {

    data.forEach((item) => {

        const card = document.querySelector(

            `[data-id="${item.partido_id}"]`

        );

        if(card){

            const botones = card.querySelectorAll(

                ".opcion"

            );

            botones.forEach((btn) => {

                if(

                    btn.innerText.trim()

                    ===

                    item.seleccion

                ){

                    btn.classList.add(

                        "seleccionado"

                    );

                }else{

                    btn.classList.add(

                        "apagado"

                    );

                }

            });

        }

    });

});

function actualizarContador(){

    const seleccionados = document.querySelectorAll(

        ".seleccionado"

    ).length;

    const total = cards.length;

    const contador = document.getElementById(

        "contador"

    );

    if(contador){

        contador.innerText =

            `${seleccionados}/${total}`;

    }

}

actualizarContador();

cards.forEach((card) => {

    const botones = card.querySelectorAll(

        ".opcion"

    );

    botones.forEach((btn) => {

        btn.addEventListener("click", () => {

            setTimeout(() => {

                actualizarContador();

            }, 50);

        });

    });

});

function mostrarToast(

    mensaje,

    tipo

){

    const toast = document.createElement(

        "div"

    );

    toast.className =

        `toast ${tipo}`;

    toast.innerText = mensaje;

    document.body.appendChild(

        toast

    );

    setTimeout(() => {

        toast.classList.add(

            "show"

        );

    }, 50);

    setTimeout(() => {

        toast.classList.remove(

            "show"

        );

        setTimeout(() => {

            toast.remove();

        }, 300);

    }, 2500);

}