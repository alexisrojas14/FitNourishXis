document.addEventListener("DOMContentLoaded", () => {
  fetch("/profile/myprofile/data")
    .then((response) => response.json())
    .then((data) => {
      if (data.error) {
        console.error("Error al obtener datos:", data.error);
        return;
      }

      // Rellenar los campos del formulario con los datos obtenidos
      document.getElementById("nombre").value = data.nombre || "";
      document.getElementById("correo").value = data.correo || "";
      document.getElementById("edad").value = data.edad || "";
      document.getElementById("peso").value = data.peso || "";
      document.getElementById("altura").value = data.altura || "";
      document.getElementById("objetivo").value = data.objetivo || "";
    })
    .catch((error) => console.error("Error en la solicitud:", error));
});
