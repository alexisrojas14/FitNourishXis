// Verificar si Firebase está correctamente inicializado
document.addEventListener("DOMContentLoaded", function () {
  if (typeof firebase === "undefined") {
    console.error("Firebase no está inicializado correctamente");
    alert(
      "Error: No se pudo inicializar Firebase. Por favor, recarga la página."
    );
    return;
  }

  if (typeof firebase.auth === "undefined") {
    console.error("Firebase auth no está disponible");
    alert("Error: No se pudo cargar el módulo de autenticación de Firebase.");
    return;
  }

  console.log("Firebase inicializado correctamente");
});

// Login con Google
document.getElementById("googleLogin").addEventListener("click", function (e) {
  e.preventDefault();
  console.log("Botón de Google clickeado");

  try {
    const provider = new firebase.auth.GoogleAuthProvider();
    provider.setCustomParameters({ prompt: "select_account" });

    firebase
      .auth()
      .signInWithPopup(provider)
      .then(function (result) {
        handleGoogleSignInResult(result);
      })
      .catch(function (error) {
        console.warn("Error con popup, intentando redirección:", error);

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

// Manejar resultado del login (popup o redirección)
function handleGoogleSignInResult(result) {
  if (result && result.user) {
    const user = result.user;
    const isNewUser = result.additionalUserInfo
      ? result.additionalUserInfo.isNewUser
      : false;

    console.log("Usuario autenticado con Google:", user.email);

    user.getIdToken().then(function (idToken) {
      console.log("Token obtenido, enviando al servidor...");

      fetch("/google-auth", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token: idToken, isNewUser: isNewUser }),
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
    if (error.code && error.code !== "auth/credential-already-in-use") {
      console.error("Error al completar inicio de sesión con Google:", error);
      alert("Error al iniciar sesión con Google: " + error.message);
    }
  });
