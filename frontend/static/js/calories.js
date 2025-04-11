document.addEventListener("DOMContentLoaded", () => {
  // Elementos del DOM
  const caloriesForm = document.getElementById("calories-form");
  const resultsDiv = document.getElementById("results");
  const loadingDiv = document.getElementById("loading-data");
  const recalculateBtn = document.getElementById("recalculate");

  // Cargar datos del perfil del usuario
  loadUserData();

  // Event Listeners
  caloriesForm.addEventListener("submit", handleCalculation);
  recalculateBtn.addEventListener("click", resetCalculator);

  // Función para cargar datos del usuario
  function loadUserData() {
    loadingDiv.classList.remove("d-none");

    fetch("/profile/myprofile/data")
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          console.error("Error al obtener datos:", data.error);
          return;
        }

        // Rellenar los campos del formulario con los datos obtenidos
        document.getElementById("edad").value = data.edad || "";
        document.getElementById("peso").value = data.peso || "";
        document.getElementById("altura").value = data.altura || "";
        document.getElementById("objetivo").value = data.objetivo || "";
      })
      .catch((error) => console.error("Error en la solicitud:", error))
      .finally(() => {
        loadingDiv.classList.add("d-none");
      });
  }

  // Función para manejar el cálculo
  function handleCalculation(event) {
    event.preventDefault();

    // Recopilar datos del formulario
    const formData = new FormData(caloriesForm);
    const userData = {
      genero: formData.get("genero"),
      edad: parseInt(formData.get("edad")),
      peso: parseFloat(formData.get("peso")),
      unidad_peso: formData.get("unidad_peso"),
      altura: parseFloat(formData.get("altura")),
      unidad_altura: formData.get("unidad_altura"),
      nivel_actividad: formData.get("nivel_actividad"),
      objetivo: formData.get("objetivo"),
    };

    // Convertir unidades si es necesario
    if (userData.unidad_peso === "lb") {
      userData.peso = userData.peso * 0.453592; // libras a kg
    }

    if (userData.unidad_altura === "in") {
      userData.altura = userData.altura * 2.54; // pulgadas a cm
    } else if (userData.unidad_altura === "m") {
      userData.altura = userData.altura * 100; // metros a cm
    }

    // Enviar datos al servidor
    fetch("/calories/calculate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(userData),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          console.error("Error en el cálculo:", data.error);
          return;
        }

        // Mostrar resultados
        displayResults(data);
      })
      .catch((error) => console.error("Error en la solicitud:", error));
  }

  // Función para mostrar los resultados
  function displayResults(data) {
    // Actualizar los elementos HTML con los resultados
    document.getElementById("tmb-result").textContent = Math.round(data.tmb);
    document.getElementById("calories-result").textContent = Math.round(
      data.calorias_diarias
    );

    document.getElementById("protein-result").textContent = `${Math.round(
      data.proteinas
    )}g`;
    document.getElementById(
      "protein-percent"
    ).textContent = `${data.porcentaje_proteinas}%`;

    document.getElementById("carbs-result").textContent = `${Math.round(
      data.carbohidratos
    )}g`;
    document.getElementById(
      "carbs-percent"
    ).textContent = `${data.porcentaje_carbohidratos}%`;

    document.getElementById("fat-result").textContent = `${Math.round(
      data.grasas
    )}g`;
    document.getElementById(
      "fat-percent"
    ).textContent = `${data.porcentaje_grasas}%`;

    // Mostrar la sección de resultados
    resultsDiv.classList.remove("d-none");
    caloriesForm.classList.add("d-none");
  }

  // Función para reiniciar la calculadora
  function resetCalculator() {
    resultsDiv.classList.add("d-none");
    caloriesForm.classList.remove("d-none");
  }
});
