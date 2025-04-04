// Validación de coincidencia de contraseñas
document
  .getElementById("registerForm")
  .addEventListener("submit", function (e) {
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm-password").value;

    if (password !== confirmPassword) {
      e.preventDefault();
      alert("Las contraseñas no coinciden");
    }
  });

// Configurar registro con Google
document.getElementById("googleSignup").addEventListener("click", function () {
  if (!firebase.apps.length) {
    // Inicializar Firebase si no está inicializado
    firebase.initializeApp({
      apiKey: "YOUR_API_KEY",
      authDomain: "YOUR_AUTH_DOMAIN",
      projectId: "YOUR_PROJECT_ID",
    });
  }
  const provider = new firebase.auth.GoogleAuthProvider();

  // Forzar selección de cuenta
  provider.setCustomParameters({
    prompt: "select_account",
  });

  // Usar signInWithRedirect en lugar de signInWithPopup para evitar bloqueos
  firebase
    .auth()
    .signInWithRedirect(provider)
    .then(function () {
      // Este código no se ejecutará inmediatamente debido a la redirección
      console.log("Redirigiendo a Google");
    })
    .catch(function (error) {
      console.error("Error al iniciar redirección con Google:", error);
      alert("Error al registrarse con Google. Por favor, intenta nuevamente.");
    });
});

// Manejar el resultado de la redirección
firebase
  .auth()
  .getRedirectResult()
  .then(function (result) {
    if (result.user) {
      // El usuario ha iniciado sesión con éxito
      const user = result.user;
      const isNewUser = result.additionalUserInfo
        ? result.additionalUserInfo.isNewUser
        : true;

      // Obtener token ID
      user.getIdToken().then(function (idToken) {
        // Enviar el token a nuestro backend para verificar y registrar
        fetch("/google-auth", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token: idToken, isNewUser: isNewUser }),
        })
          .then((response) => response.json())
          .then((data) => {
            if (data.success) {
              window.location.href = "/principal";
            }
          })
          .catch((error) => {
            console.error("Error al enviar token al servidor:", error);
          });
      });
    }
  })
  .catch(function (error) {
    if (error.code !== "auth/credential-already-in-use") {
      console.error("Error al completar registro con Google:", error);
      // Solo mostrar alerta si hay un error real (no durante la carga inicial)
      if (error.code) {
        alert("Error al registrarse con Google: " + error.message);
      }
    }
  });
