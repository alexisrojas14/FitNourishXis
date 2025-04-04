// Verificar si Firebase está correctamente inicializado
document.addEventListener("DOMContentLoaded", function () {
  // Comprobar si firebase está disponible
  if (typeof firebase === "undefined") {
    console.error("Firebase no está inicializado correctamente");
    alert(
      "Error: No se pudo inicializar Firebase. Por favor, recarga la página."
    );
    return;
  }

  // Comprobar si firebase.auth está disponible
  if (typeof firebase.auth === "undefined") {
    console.error("Firebase auth no está disponible");
    alert("Error: No se pudo cargar el módulo de autenticación de Firebase.");
    return;
  }

  console.log("Firebase inicializado correctamente");
});

// Configurar autenticación de Google para inicio de sesión
document.getElementById("googleLogin").addEventListener("click", function (e) {
  e.preventDefault(); // Prevenir comportamiento por defecto del botón

  console.log("Botón de Google clickeado");

  try {
    const provider = new firebase.auth.GoogleAuthProvider();

    // Forzar selección de cuenta
    provider.setCustomParameters({
      prompt: "select_account",
    });

    console.log("Iniciando proceso de autenticación con Google...");

    // Intentar primero con popup (más amigable con el usuario)
    firebase
      .auth()
      .signInWithPopup(provider)
      .then(function (result) {
        handleGoogleSignInResult(result);
      })
      .catch(function (error) {
        console.warn("Error con popup, intentando redirección:", error);

        // Si falla el popup, usar redirección como fallback
        firebase
          .auth()
          .signInWithRedirect(provider)
          .then(function () {
            console.log("Redirigiendo a Google");
          })
          .catch(function (error) {
            console.error("Error crítico al iniciar sesión con Google:", error);
            alert(
              "Error al iniciar sesión con Google. Por favor, intenta nuevamente."
            );
          });
      });
  } catch (error) {
    console.error("Error al configurar autenticación con Google:", error);
    alert("Error al configurar la autenticación con Google.");
  }
});

// Manejar el resultado de la redirección o popup
function handleGoogleSignInResult(result) {
  if (result && result.user) {
    // El usuario ha iniciado sesión con éxito
    const user = result.user;
    const isNewUser = result.additionalUserInfo
      ? result.additionalUserInfo.isNewUser
      : false;

    console.log("Usuario autenticado con Google:", user.email);

    // Obtener token ID
    user
      .getIdToken()
      .then(function (idToken) {
        console.log("Token obtenido, enviando al servidor...");

        // Enviar el token a nuestro backend para verificar
        return fetch("/google-auth", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token: idToken,
            isNewUser: isNewUser,
          }),
        });
      })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Error del servidor: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.success) {
          console.log("Autenticación exitosa, redirigiendo...");
          window.location.href = "/principal";
        } else {
          console.error("Error en respuesta del servidor:", data.error);
          alert(
            "Error al verificar la autenticación. Por favor, intenta nuevamente."
          );
        }
      })
      .catch((error) => {
        console.error("Error al procesar la autenticación:", error);
        alert(
          "Error al procesar la autenticación. Por favor, intenta nuevamente."
        );
      });
  } else {
    console.warn(
      "No se obtuvo información de usuario después de la autenticación"
    );
  }
}

// Verificar resultado de redirección al cargar la página
firebase
  .auth()
  .getRedirectResult()
  .then(function (result) {
    if (result.user) {
      handleGoogleSignInResult(result);
    }
  })
  .catch(function (error) {
    // Ignorar errores cuando no hay redirección previa
    if (error.code && error.code !== "auth/credential-already-in-use") {
      console.error("Error al completar inicio de sesión con Google:", error);
      alert("Error al iniciar sesión con Google: " + error.message);
    }
  });
