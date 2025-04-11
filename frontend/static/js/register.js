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
  const provider = new firebase.auth.GoogleAuthProvider();

  provider.setCustomParameters({
    prompt: "select_account",
  });

  firebase
    .auth()
    .signInWithRedirect(provider)
    .then(function () {
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
      const user = result.user;
      const isNewUser = result.additionalUserInfo
        ? result.additionalUserInfo.isNewUser
        : true;

      user.getIdToken().then(function (idToken) {
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
            } else {
              console.error("Error en la respuesta del servidor:", data.error);
              alert("Error al registrar usuario con Google.");
            }
          })
          .catch((error) => {
            console.error("Error al enviar token al servidor:", error);
            alert("Error al procesar el registro con Google.");
          });
      });
    }
  })
  .catch(function (error) {
    if (error.code && error.code !== "auth/credential-already-in-use") {
      console.error("Error al completar registro con Google:", error);
      alert("Error al registrarse con Google: " + error.message);
    }
  });
