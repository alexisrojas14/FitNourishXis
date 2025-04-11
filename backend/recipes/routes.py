from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from db import get_connection
import requests
import os
from dotenv import load_dotenv

load_dotenv()

recipes_bp = Blueprint('recipes', __name__)

@recipes_bp.route('/recipes', methods=['GET'])
def index():
    """Renderiza la página principal de recetas."""
    return render_template('recipes.html')


@recipes_bp.route('/recipes/add', methods=['GET', 'POST'])
def add():
    """Agregar una nueva receta a la base de datos."""
    if request.method == 'GET':
        return render_template('add_recipe.html')

    firebase_uid = session.get('user_id')
    if not firebase_uid:
        return jsonify({"error": "Usuario no autenticado"}), 401

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE firebase_uid = %s", (firebase_uid,))
            result = cursor.fetchone()
            if not result:
                return jsonify({"error": "Usuario no encontrado"}), 404

            id_usuario = result[0]
            nombre = request.form.get('nombre')
            ingredientes = request.form.get('ingredientes')
            instrucciones = request.form.get('instrucciones')
            info_nutricional = request.form.get('info_nutricional', '')
            fuente = "Usuario"

            if not nombre or not ingredientes or not instrucciones:
                return jsonify({"error": "Todos los campos son obligatorios"}), 400

            sql = """
                INSERT INTO recetas (nombre, ingredientes, instrucciones, info_nutricional, fuente, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (nombre, ingredientes, instrucciones, info_nutricional, fuente, id_usuario))
            connection.commit()

        return redirect(url_for('recipes.index'))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


@recipes_bp.route('/favorites', methods=['POST', 'DELETE'])
def manage_favorites():
    """Agregar o eliminar recetas de favoritos."""
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        return jsonify({"error": "Usuario no autenticado"}), 401

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            # Obtener el ID del usuario desde la base de datos
            cursor.execute("SELECT id_usuario FROM usuarios WHERE firebase_uid = %s", (firebase_uid,))
            user_row = cursor.fetchone()
            if not user_row:
                return jsonify({"error": "Usuario no encontrado"}), 404
            id_usuario = user_row[0]

            data = request.json
            id_receta = data.get('id_receta')
            is_user_recipe = data.get('is_user_recipe', False)

            if request.method == 'POST':
                # Si la receta no es de un usuario, verificar si es de la API
                if not is_user_recipe:
                    # Verificar si la receta ya existe en la base de datos
                    cursor.execute("SELECT id_receta FROM recetas WHERE id_receta = %s", (id_receta,))
                    existing_recipe = cursor.fetchone()

                    if not existing_recipe:
                        # Obtener detalles de la receta desde la API
                        recipe_details = get_recipe_details_from_api(id_receta)
                        if "error" in recipe_details:
                            return jsonify({"error": recipe_details["error"]}), 500

                        # Guardar la receta en la base de datos
                        sql = """
                            INSERT INTO recetas (id_receta, nombre, ingredientes, instrucciones, info_nutricional, fuente, id_usuario)
                            VALUES (%s, %s, %s, %s, %s, %s, NULL)
                        """
                        cursor.execute(sql, (
                            recipe_details["id_receta"],
                            recipe_details["nombre"],
                            recipe_details["ingredientes"],
                            recipe_details["instrucciones"],
                            recipe_details["info_nutricional"],
                            recipe_details["fuente"]
                        ))
                        connection.commit()

                # Agregar la receta a favoritos
                sql = """
                    INSERT INTO favoritos (id_usuario, id_receta)
                    VALUES (%s, %s)
                """
                cursor.execute(sql, (id_usuario, id_receta))
                connection.commit()
                return jsonify({"message": "Receta agregada a favoritos"}), 201

            elif request.method == 'DELETE':
                # Eliminar la receta de favoritos
                sql = """
                    DELETE FROM favoritos
                    WHERE id_usuario = %s AND id_receta = %s
                """
                cursor.execute(sql, (id_usuario, id_receta))
                connection.commit()
                return jsonify({"message": "Receta eliminada de favoritos"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()


def get_recipe_details_from_api(recipe_id):
    """Obtener detalles completos de una receta desde la API."""
    api_key = os.environ.get('SPOONACULAR_API_KEY')
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information?apiKey={api_key}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        recipe_details = response.json()
        return {
            "id_receta": recipe_details.get('id'),
            "nombre": recipe_details.get('title'),
            "ingredientes": ", ".join(
                [ingredient['original'] for ingredient in recipe_details.get('extendedIngredients', [])]
            ),
            "instrucciones": recipe_details.get('instructions', "No disponible"),
            "info_nutricional": "No disponible",
            "fuente": recipe_details.get('sourceUrl'),
            "imagen": recipe_details.get('image'),
        }
    except requests.exceptions.RequestException as e:
        return {"error": f"Error al obtener detalles de la receta: {str(e)}"}


@recipes_bp.route('/recipes/random', methods=['GET'])
def get_random_recipes():
    """Obtener recetas aleatorias desde la API con detalles completos."""
    api_key = os.environ.get('SPOONACULAR_API_KEY')
    url = f"https://api.spoonacular.com/recipes/random?apiKey={api_key}&number=5"

    try:
        response = requests.get(url)
        response.raise_for_status()
        api_recipes = response.json().get('recipes', [])
        recipes = [get_recipe_details_from_api(recipe.get('id')) for recipe in api_recipes]
        return jsonify(recipes)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error al obtener recetas aleatorias: {str(e)}"}), 500


@recipes_bp.route('/recipes/category', methods=['GET'])
def get_recipes_by_category():
    """Obtener recetas por categoría desde la API con detalles completos."""
    category = request.args.get('category', 'main course')
    api_key = os.environ.get('SPOONACULAR_API_KEY')
    url = f"https://api.spoonacular.com/recipes/complexSearch?apiKey={api_key}&type={category}&number=10"

    try:
        response = requests.get(url)
        response.raise_for_status()
        api_recipes = response.json().get('results', [])
        recipes = [get_recipe_details_from_api(recipe.get('id')) for recipe in api_recipes]
        return jsonify(recipes)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error al obtener recetas por categoría: {str(e)}"}), 500


@recipes_bp.route('/filter', methods=['GET'])
def filter_recipes():
    """Filtrar recetas según el tipo."""
    firebase_uid = session.get('user_id')
    if not firebase_uid:
        return jsonify({"error": "Usuario no autenticado"}), 401

    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id_usuario FROM usuarios WHERE firebase_uid = %s", (firebase_uid,))
            user_row = cursor.fetchone()
            if not user_row:
                return jsonify({"error": "Usuario no encontrado"}), 404
            id_usuario = user_row[0]

            filter_type = request.args.get('filter', 'all')

            if filter_type == 'favorites':
                sql = """
                    SELECT r.id_receta, r.nombre, r.ingredientes, r.instrucciones, r.info_nutricional, r.fuente
                    FROM favoritos f
                    JOIN recetas r ON f.id_receta = r.id_receta
                    WHERE f.id_usuario = %s
                """
                cursor.execute(sql, (id_usuario,))
                recipes = cursor.fetchall()

                return jsonify([
                    {
                        "id_receta": row[0],
                        "nombre": row[1],
                        "ingredientes": row[2],
                        "instrucciones": row[3],
                        "info_nutricional": row[4],
                        "fuente": row[5],
                    }
                    for row in recipes
                ])

            elif filter_type == 'user_recipes':
                sql = """
                    SELECT id_receta, nombre, ingredientes, instrucciones, info_nutricional, fuente
                    FROM recetas
                    WHERE id_usuario = %s
                """
                cursor.execute(sql, (id_usuario,))
                recipes = cursor.fetchall()

                return jsonify([
                    {
                        "id_receta": row[0],
                        "nombre": row[1],
                        "ingredientes": row[2],
                        "instrucciones": row[3],
                        "info_nutricional": row[4],
                        "fuente": row[5],
                    }
                    for row in recipes
                ])

            elif filter_type == 'usuarios':
                sql = """
                    SELECT r.id_receta, r.nombre, r.ingredientes, r.instrucciones, r.info_nutricional, r.fuente, u.nombre AS autor
                    FROM recetas r
                    JOIN usuarios u ON r.id_usuario = u.id_usuario
                """
                cursor.execute(sql)
                recipes = cursor.fetchall()

                return jsonify([
                    {
                        "id_receta": row[0],
                        "nombre": row[1],
                        "ingredientes": row[2],
                        "instrucciones": row[3],
                        "info_nutricional": row[4],
                        "fuente": row[5],
                        "autor": row[6] if len(row) > 6 else "Desconocido"
                    }
                    for row in recipes
                ])

            elif filter_type == 'all':
                sql = """
                    SELECT id_receta, nombre, ingredientes, instrucciones, info_nutricional, fuente
                    FROM recetas
                """
                cursor.execute(sql)
                db_recipes = cursor.fetchall()

                formatted_db_recipes = [
                    {
                        "id_receta": row[0],
                        "nombre": row[1],
                        "ingredientes": row[2],
                        "instrucciones": row[3],
                        "info_nutricional": row[4],
                        "fuente": row[5],
                    }
                    for row in db_recipes
                ]

                try:
                    api_key = os.environ.get('SPOONACULAR_API_KEY')
                    url = f"https://api.spoonacular.com/recipes/random?apiKey={api_key}&number=5"
                    response = requests.get(url)
                    response.raise_for_status()
                    api_recipes = response.json().get('recipes', [])

                    formatted_api_recipes = [get_recipe_details_from_api(recipe.get('id')) for recipe in api_recipes]

                    return jsonify(formatted_db_recipes + formatted_api_recipes)
                except:
                    return jsonify(formatted_db_recipes)

            else:
                return jsonify([])

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        connection.close()