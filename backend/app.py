from flask import Flask, render_template, request, redirect, url_for, jsonify, session # Importar Flask y otros módulos necesarios
import firebase_admin  # Importar Firebase Admin SDK
from firebase_admin import credentials, auth # Importar Firebase Admin SDK
import logging
import pyrebase.pyrebase as pyrebase 
import requests # Importar Flask y otros módulos necesarios
import json # Importar requests y json para manejar solicitudes HTTP y JSON
from dotenv import load_dotenv # Importar dotenv para cargar variables de entorno
import os # Importar os para cargar variables de entorno
from db import get_connection # Importar la función de conexión a la base de datos
from profile.routes import profile_bp # Importar el blueprint de perfil
from utils import get_firebase_uid  # Importar la función desde utils.py




load_dotenv() # Cargar variables de entorno desde el archivo .env

# Configuración de Firebase
config = {      
    "apiKey": os.environ.get('API_KEY'),
    "authDomain": os.environ.get('AUTH_DOMAIN'),
    "databaseURL": os.environ.get('DATABASE_URL'),
    "projectId": os.environ.get('PROJECT_ID'),
    "storageBucket": os.environ.get('STORAGE_BUCKET'),
}


# Configuración de logging más detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Inicialización de Firebase Admin
try:
    cred = credentials.Certificate(os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')) # Ruta al archivo de credenciales
    firebase_app = firebase_admin.initialize_app(cred) # Inicializar Firebase Admin con las credenciales
    logger.info("Firebase Admin inicializado correctamente") #aviso inicializacion firebase
except Exception as e:
    logger.error(f"Error al inicializar Firebase Admin: {e}")
    raise

# Inicialización de Pyrebase
try:
    firebase = pyrebase.initialize_app(config) # Inicializar Pyrebase con la configuración
    logger.info("Pyrebase inicializado correctamente") #aviso inicializacion pyrebase
except Exception as e:
    logger.error(f"Error al inicializar Pyrebase: {e}")
    raise

app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static') # Inicializar Flask
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24)) # Clave secreta para la sesión de Flask
app.register_blueprint(profile_bp,url_prefix="/profile") # Registrar el blueprint de perfil

@app.route('/', methods=['GET', 'POST'])
def index(): # Ruta principal
    return redirect(url_for('login'))# Redirigir a la página de inicio de sesión

@app.route('/register', methods=['GET', 'POST'])
def register():  # Ruta de registro
    if request.method == 'GET':  # Si se accede a la página de registro
        return render_template('register.html')  # Renderizar la plantilla de registro
    elif request.method == 'POST':  # Si se envía el formulario de registro
        email = request.form['email']
        password = request.form['password']
        
        try:
            # Crear un nuevo usuario en Firebase Auth
            user = auth.create_user(email=email, password=password)
            logger.info(f"Usuario creado en Firebase: {user.uid}")  # Aviso de creación de usuario
            
            # Guardar el usuario en la base de datos MySQL
            connection = get_connection()
            with connection.cursor() as cursor:
                query = """
                    INSERT INTO usuarios (firebase_uid, correo)
                    VALUES (%s, %s)
                """
                cursor.execute(query, (user.uid, email))
                connection.commit()
                logger.info(f"Usuario guardado en la base de datos MySQL: {user.uid}")
            
            return redirect(url_for('login'))  # Redirigir a la página de inicio de sesión
        except Exception as e:
            logger.error(f"Error al registrar usuario: {e}")
            return render_template('register.html', error=str(e))

@app.route('/login', methods=['GET', 'POST'])   
def login(): # Ruta de inicio de sesión

    mensaje = request.args.get('mensaje')  

    if request.method == 'GET':
        return render_template('login.html') # Renderizar la plantilla de inicio de sesión
    elif request.method == 'POST': # Si se envía el formulario de inicio de sesión
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = firebase.auth().sign_in_with_email_and_password(email, password) # Autenticar al usuario con Firebase Auth
            logger.info(f"Usuario autenticado con email/password") # Aviso de autenticación
            
            # Obtener el UID del usuario autenticado
            user_info = firebase.auth().get_account_info(user['idToken'])
            uid = user_info['users'][0]['localId']
            
            # Verificar si el UID está en la base de datos MySQL
            connection = get_connection()
            with connection.cursor() as cursor:
                query = "SELECT * FROM usuarios WHERE firebase_uid = %s"
                cursor.execute(query, (uid,))
                result = cursor.fetchone()
                
                if not result:
                    # Si el UID no está en la base de datos, guardarlo
                    query = """
                        INSERT INTO usuarios (firebase_uid, correo)
                        VALUES (%s, %s)
                    """
                    cursor.execute(query, (uid, email))
                    connection.commit()
                    logger.info(f"Usuario guardado en la base de datos MySQL: {uid}")
            
            # Guardar token de usuario en la sesión
            session['user_token'] = user['idToken']
            session['user_id'] = uid
            session['user_email'] = email
            
            
            return redirect(url_for('principal')) # Redirigir a la página principal
        except Exception as e:
            logger.error(f"Error al autenticar usuario: {e}")
            error_message = "Credenciales inválidas. Por favor, verifica tu correo y contraseña."
            return render_template('login.html', error=error_message, mensaje=mensaje) # Renderizar la plantilla de inicio de sesión con error

@app.route('/google-auth', methods=['POST'])
def google_auth():
    logger.info("Recibida solicitud de autenticación de Google")
    
    try:
        data = request.json
        if not data:
            logger.error("No se recibieron datos JSON")
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400
            
        id_token = data.get('token', '')
        if not id_token:
            logger.error("No se recibió token de ID")
            return jsonify({"success": False, "error": "Token no proporcionado"}), 400
            
        is_new_user = data.get('isNewUser', False)
        logger.info(f"Token recibido, verificando... (isNewUser: {is_new_user})")
        
        decoded_token = auth.verify_id_token(id_token)
        uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        display_name = decoded_token.get('name', '')
        
        logger.info(f"Token verificado correctamente: {uid} ({email})")

        try:
            user = auth.get_user(uid)
            logger.info(f"Usuario existente en Firebase Auth: {user.uid}")
        except auth.UserNotFoundError:
            if is_new_user:
                user = auth.create_user(
                    uid=uid,
                    email=email,
                    email_verified=True,
                    display_name=display_name
                )
                logger.info(f"Nuevo usuario creado: {user.uid}")
            else:
                logger.error("Usuario no encontrado y no es nuevo usuario")
                return jsonify({"success": False, "error": "Usuario no encontrado"}), 404
        
        # CONEXIÓN Y VERIFICACIÓN EN MYSQL
        connection = get_connection()
        with connection.cursor() as cursor:
            query = "SELECT * FROM usuarios WHERE firebase_uid = %s"
            cursor.execute(query, (uid,))
            result = cursor.fetchone()

            if not result:
                # Insertar usuario en MySQL si no existe
                insert_query = """
                    INSERT INTO usuarios (firebase_uid, correo)
                    VALUES (%s, %s)
                """
                cursor.execute(insert_query, (uid, email))
                connection.commit()
                logger.info(f"Usuario guardado en la base de datos MySQL: {uid}")

         # Guardar datos en la sesión
        session['user_id'] = decoded_token['uid']
        session['user_token'] = id_token
        session['user_email'] = decoded_token['email']
        
        logger.info(f"Sesión creada para {uid}, autenticación exitosa")
        return jsonify({"success": True})
    
    except auth.InvalidIdTokenError as e:
        logger.error(f"Token inválido: {e}")
        return jsonify({"success": False, "error": "Token inválido o expirado"}), 401
    except Exception as e:
        logger.error(f"Error verificando token de Google: {e}")
        return jsonify({"success": False, "error": str(e)}), 400


@app.route('/principal', methods=['GET'])
def principal(): # Ruta de la página principal
    # Verificar si el usuario está autenticado
    if 'user_id' not in session and 'user_token' not in session: # Si no hay sesión activa
        logger.warning("Intento de acceso a /principal sin autenticación")
        return redirect(url_for('login')) # Redirigir a la página de inicio de sesión
    
    firebaseuid = session.get('user_id') # Obtener el UID del usuario autenticado desde la 
    if not firebaseuid:
        return redirect(url_for('login'))
    
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT nombre FROM usuarios WHERE firebase_uid = %s"
            cursor.execute(sql, (firebaseuid,))
            result = cursor.fetchone()
            nombre = result[0] if result else "Usuario"  # Si no se encuentra el nombre, usar "Usuario"
    except Exception as e:
            logger.error(f"Error al obtener el nombre del usuario: {e}")
            nombre = "Usuario"
    finally:
        connection.close()

    # Renderizar la plantilla y pasar el nombre al HTML
    return render_template('principal.html', nombre=nombre)

@app.route('/logout', methods=['GET', 'POST'])
def logout(): # Ruta para cerrar sesión
    # Eliminar datos de sesión
    session.clear()
    
    logger.info("Usuario desconectado")
    return redirect(url_for('login',mensaje='Sesion cerrada correctamente')) # Redirigir a la página de inicio de sesión


    
if __name__ == '__main__':
    logger.info("Iniciando aplicación Flask") # Aviso de inicio de aplicación
    app.run(debug=True) # Ejecutar la aplicación Flask en modo de depuración