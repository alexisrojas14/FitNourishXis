document.addEventListener("DOMContentLoaded", () => {
  const recipesContainer = document.getElementById("recipes-container");
  const messageContainer = document.getElementById("message-container");

  // Cargar todas las recetas al inicio
  loadRecipes("all");

  // Manejar los filtros
  const filterButtons = document.querySelectorAll(".filter-btn");
  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const filter = button.getAttribute("data-filter");
      const category = button.getAttribute("data-category");
      if (filter === "api_recipes") {
        loadRecipesByCategory(category);
      } else {
        loadRecipes(filter);
      }
    });
  });

  // Función para cargar recetas según el filtro
  function loadRecipes(filter) {
    recipesContainer.innerHTML = "";
    const url = `/recipes/filter?filter=${filter}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          showMessage(data.error, "danger");
          return;
        }

        data.forEach((recipe) => {
          const card = createRecipeCard(
            recipe,
            filter === "user_recipes" || filter === "favorites"
          );
          recipesContainer.appendChild(card);
        });

        setupEventListeners();
      })
      .catch((error) => {
        console.error("Error al cargar recetas:", error);
        showMessage("Error al cargar recetas. Inténtalo de nuevo.", "danger");
      });
  }

  // Función para cargar recetas por categoría desde la API
  function loadRecipesByCategory(category) {
    recipesContainer.innerHTML = "";
    const url = `/recipes/category?category=${category}`;

    fetch(url)
      .then((response) => response.json())
      .then((data) => {
        if (data.error) {
          showMessage(data.error, "danger");
          return;
        }

        data.forEach((recipe) => {
          const card = createRecipeCard(recipe, false);
          recipesContainer.appendChild(card);
        });

        setupEventListeners();
      })
      .catch((error) => {
        console.error("Error al cargar recetas por categoría:", error);
        showMessage(
          "Error al cargar recetas por categoría. Inténtalo de nuevo.",
          "danger"
        );
      });
  }

  // Crear la card de una receta
  function createRecipeCard(recipe, isUserRecipe) {
    const card = document.createElement("div");
    card.className = "col-md-4 mb-4";

    const title = recipe.nombre || recipe.title;
    const ingredientes = recipe.ingredientes || "Cargando...";
    const instrucciones = recipe.instrucciones || "Cargando...";
    const imagen =
      recipe.imagen ||
      recipe.image ||
      "https://via.placeholder.com/400x300?text=Sin+Imagen";

    card.innerHTML = `
      <div class="card h-100">
        <img src="${imagen}" class="card-img-top" alt="${title}" />
        <div class="card-body d-flex flex-column">
          <h5 class="card-title">${title}</h5>
          <p class="card-text"><strong>Ingredientes:</strong> ${ingredientes.slice(
            0,
            100
          )}...</p>
          <div class="mt-auto">
            <button class="btn btn-sm btn-outline-info me-2 view-details">Ver Detalles</button>
            <button class="btn btn-sm btn-outline-danger favorite-btn" 
              data-recipe-id="${recipe.id_receta || recipe.id}" 
              data-user-recipe="${isUserRecipe}">
              <i class="fas fa-heart"></i> Favorito
            </button>
          </div>
        </div>
      </div>
    `;

    card.querySelector(".view-details").addEventListener("click", () => {
      showRecipeDetails(recipe);
    });

    return card;
  }

  // Mostrar detalles de la receta en el modal
  function showRecipeDetails(recipe) {
    document.getElementById("modal-recipe-title").textContent =
      recipe.nombre || recipe.title;
    document.getElementById("modal-recipe-ingredients").textContent =
      recipe.ingredientes || "No disponible";
    document.getElementById("modal-recipe-instructions").textContent =
      recipe.instrucciones || "No disponible";
    document.getElementById("modal-recipe-image").src =
      recipe.imagen || "https://via.placeholder.com/400x300?text=Sin+Imagen";
    document.getElementById("modal-recipe-source").textContent =
      recipe.fuente || "Desconocida";

    const modal = new bootstrap.Modal(document.getElementById("recipeModal"));
    modal.show();
  }

  // Configurar eventos de botones de favoritos
  function setupEventListeners() {
    const favButtons = document.querySelectorAll(".favorite-btn");
    favButtons.forEach((btn) => {
      btn.addEventListener("click", () => {
        const recipeId = btn.getAttribute("data-recipe-id");
        const isUserRecipe = btn.getAttribute("data-user-recipe") === "true";

        fetch("/recipes/favorites", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            id_receta: recipeId,
            is_user_recipe: isUserRecipe,
          }),
        })
          .then((res) => res.json())
          .then((data) => {
            if (data.message) {
              showMessage(data.message, "success");
            } else {
              showMessage(
                data.error || "Error al agregar a favoritos",
                "danger"
              );
            }
          })
          .catch((err) => {
            console.error("Error al guardar favorito:", err);
            showMessage("Error inesperado.", "danger");
          });
      });
    });
  }

  // Mostrar mensajes de éxito o error
  function showMessage(message, type) {
    messageContainer.innerHTML = `
      <div class="alert alert-${type}" role="alert">
        ${message}
      </div>
    `;
    setTimeout(() => {
      messageContainer.innerHTML = "";
    }, 3000);
  }
});
