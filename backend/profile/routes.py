from venv import logger
from flask import Blueprint, jsonify, render_template, request, redirect, url_for, session
from utils import get_firebase_uid  # Importar la función desde utils.py
from db import get_connection
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

profile_bp = Blueprint('profile', __name__)



@profile_bp.route('/myprofile/data', methods=['GET'])
def get_profile_data():

    logger.info(f"Sesión actual: {session}")
    # Verificar si el usuario está autenticado
    if 'user_id' not in session:
        logger.warning("No se encontró user_id en la sesión")
        return jsonify({"error": "Usuario no autenticado"}), 401

    if 'user_token' not in session:
        logger.warning("No se encontró user_token en la sesión")
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    # Obtener el UID del usuario autenticado desde la sesión
    firebaseuid = session.get('user_id')
    user_email = session.get('user_email')

    logger.info(f"Intentando obtener datos para usuario con UID: {firebaseuid} y email: {user_email}")

   

    # Conectar a la base de datos y buscar los datos del usuario
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT nombre, correo, edad, peso, altura, objetivo FROM usuarios WHERE firebase_uid = %s"
            cursor.execute(sql, (firebaseuid,))
            user_data = cursor.fetchone()
            if user_data:
                # Mapear los datos a un diccionario y devolverlos como JSON
                keys = ["nombre", "correo", "edad", "peso", "altura", "objetivo"]
                user_data_dict = dict(zip(keys, user_data))
                return jsonify(user_data_dict)
            else:
                logger.warning(f"No se encontraron datos para el usuario con UID: {firebaseuid}")
                return jsonify({"error": "Usuario no encontrado"}), 404
    except Exception as e:
        logger.error(f"Error al obtener datos del usuario: {str(e)}")
        return jsonify({"error": f"Error al obtener datos del usuario: {str(e)}"}), 500
    finally:
        connection.close()

@profile_bp.route('/myprofile', methods=['GET'])
def myprofile():
    # Obtener el UID del usuario autenticado desde la sesión
    firebaseuid = session.get('user_id')
    if not firebaseuid:
        return redirect(url_for('login'))
    
    return render_template('myprofile.html')
    

@profile_bp.route('/update_information', methods=['GET', 'POST'])
def update_information():

    firebaseuid = session.get('user_id')
    if not firebaseuid:
        return redirect(url_for('login'))
    
    if request.method == 'GET': 
        return render_template('myprofile.html')  
    elif request.method == 'POST':  
        
        nombre = request.form['nombre']
        edad = request.form['edad']
        peso = request.form['peso']
        altura = request.form['altura']
        objetivo = request.form['objetivo']
       

        connection = get_connection()
        try:
            with connection.cursor() as cursor:
                sql = """
                UPDATE usuarios
                SET nombre = %s, edad = %s, peso = %s, altura = %s, objetivo = %s, es_nuevo = FALSE
                WHERE firebase_uid = %s
                """
                cursor.execute(sql, (nombre, edad, peso, altura, objetivo, firebaseuid))
                connection.commit()
                logger.info(f"Datos actualizados para el usuario con UID: {firebaseuid}")
            
            return redirect(url_for('principal'))  # Redirigir a la página principal
        except Exception as e:
            logger.error(f"Error al Actualizar informacion: {e}")
            return render_template('myprofile.html', error=str(e))