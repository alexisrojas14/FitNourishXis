document.addEventListener("DOMContentLoaded", () => {
  const logoutLink = document.getElementById("logout-link");

  if (logoutLink) {
    logoutLink.addEventListener("click", (event) => {
      event.preventDefault();

      firebase
        .auth()
        .signOut()
        .then(() => {
          console.log("Sesión Firebase cerrada");

          // Limpieza visual (opcional)
          const alert = document.getElementById("logout-alert");
          if (alert) {
            alert.style.display = "block";
          }

          // Redirige al logout de Flask que limpia la sesión
          setTimeout(() => {
            window.location.href = logoutLink.dataset.logoutUrl;
          }, 1500); // 1.5 segundos está bien
        })
        .catch((error) => {
          console.error("Error al cerrar sesión en Firebase:", error);
        });
    });
  }
});
