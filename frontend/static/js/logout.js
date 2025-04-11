document.addEventListener("DOMContentLoaded", () => {
  const logoutLink = document.getElementById("logout-link");

  if (logoutLink) {
    logoutLink.addEventListener("click", async (event) => {
      event.preventDefault();

      try {
        // 1. Cerrar sesión en Firebase
        await firebase.auth().signOut();
        console.log("Sesión Firebase cerrada");

        // 2. Limpiar localStorage y sessionStorage
        localStorage.clear();
        sessionStorage.clear();
        console.log("Almacenamiento local limpiado");

        // 3. Limpiar cookies relacionadas con la sesión
        document.cookie.split(";").forEach((cookie) => {
          const name = cookie.trim().split("=")[0];
          document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        });
        console.log("Cookies limpiadas");

        // 4. Mostrar alerta de cierre de sesión
        const alert = document.getElementById("logout-alert");
        if (alert) {
          alert.style.display = "block";
          alert.textContent = "Cerrando sesión...";
        }

        // 5. Redirigir al endpoint de logout de Flask
        setTimeout(() => {
          // Hacer una petición POST al endpoint de logout
          fetch(logoutLink.dataset.logoutUrl, {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Content-Type": "application/json",
            },
          })
            .then(() => {
              console.log("Sesión del servidor limpiada");
              window.location.href = "/login"; // Redirigir a la página de login
            })
            .catch((error) => {
              console.error("Error al limpiar la sesión del servidor:", error);
              window.location.href = "/login"; // Redirigir de todos modos
            });
        }, 1000);
      } catch (error) {
        console.error("Error durante el proceso de logout:", error);
        // Redirigir a login incluso si hay error
        window.location.href = "/login";
      }
    });
  }
});
