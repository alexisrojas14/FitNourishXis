from flask import Flask, render_template, request, redirect, url_for, jsonify, session # Importar Flask y otros módulos necesarios
import firebase_admin  # Importar Firebase Admin SDK
from firebase_admin import credentials, auth # Importar Firebase Admin SDK
import logging
import pyrebase.pyrebase as pyrebase 
import requests # Importar Flask y otros módulos necesarios
import json # Importar requests y json para manejar solicitudes HTTP y JSON
from dotenv import load_dotenv # Importar dotenv para cargar variables de entorno
import os # Importar os para cargar variables de entorno


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

@app.route('/', methods=['GET', 'POST'])
def index(): # Ruta principal
    return redirect(url_for('login'))# Redirigir a la página de inicio de sesión

@app.route('/register', methods=['GET', 'POST'])
def register():# Ruta de registro
    if request.method == 'GET': # Si se accede a la página de registro
        return render_template('register.html')# Renderizar la plantilla de registro
    elif request.method == 'POST': # Si se envía el formulario de registro
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = auth.create_user(email=email, password=password) # Crear un nuevo usuario en Firebase Auth
            logger.info(f"Usuario creado: {user.uid}")  # Aviso de creación de usuario
            return redirect(url_for('login')) # Redirigir a la página de inicio de sesión
        except Exception as e:
            logger.error(f"Error al crear usuario: {e}")
            return render_template('register.html', error=str(e))

@app.route('/login', methods=['GET', 'POST'])   
def login(): # Ruta de inicio de sesión
    if request.method == 'GET':
        return render_template('login.html') # Renderizar la plantilla de inicio de sesión
    elif request.method == 'POST': # Si se envía el formulario de inicio de sesión
        email = request.form['email']
        password = request.form['password']
        
        try:
            user = firebase.auth().sign_in_with_email_and_password(email, password) # Autenticar al usuario con Firebase Auth
            logger.info(f"Usuario autenticado con email/password") # Aviso de autenticación
            # Guardar token de usuario en la sesión
            session['user_token'] = user['idToken']
            return redirect(url_for('principal')) # Redirigir a la página principal
        except Exception as e:
            logger.error(f"Error al autenticar usuario: {e}")
            error_message = "Credenciales inválidas. Por favor, verifica tu correo y contraseña."
            return render_template('login.html', error=error_message)

@app.route('/google-auth', methods=['POST'])
def google_auth(): # Ruta para manejar la autenticación de Google
    # Obtener el token ID de Google
    logger.info("Recibida solicitud de autenticación de Google")
    
    try:
        data = request.json # Obtener datos JSON de la solicitud
        if not data:
            logger.error("No se recibieron datos JSON")
            return jsonify({"success": False, "error": "No se recibieron datos"}), 400
            
        id_token = data.get('token', '') # Obtener el token ID de los datos JSON
        if not id_token:
            logger.error("No se recibió token de ID")
            return jsonify({"success": False, "error": "Token no proporcionado"}), 400
            
        is_new_user = data.get('isNewUser', False) # Verificar si es un nuevo usuario
        
        logger.info(f"Token recibido, verificando... (isNewUser: {is_new_user})")  # Aviso de token recibido
        
        # Verificar el token ID con Firebase Auth
        decoded_token = auth.verify_id_token(id_token) # Verificar el token ID
        uid = decoded_token['uid'] # Obtener el UID del token
        email = decoded_token.get('email', '') # Obtener el correo electrónico del token
        
        logger.info(f"Token verificado correctamente: {uid} ({email})") # Aviso de token verificado
        
        # Verificar si el usuario ya existe o crear uno nuevo
        try:
            user = auth.get_user(uid) # Intentar obtener el usuario por UID
            # Si el usuario ya existe, no hacemos nada
            logger.info(f"Usuario existente: {user.uid}")
        except auth.UserNotFoundError:
            # Si el usuario no existe y estamos en el flujo de registro
            if is_new_user:
                # Crear el usuario en Firebase Auth
                display_name = decoded_token.get('name', '') # Obtener el nombre del usuario del token
                
                user = auth.create_user(  ## Crear un nuevo usuario en Firebase Auth
                    uid=uid,
                    email=email,
                    email_verified=True,
                    display_name=display_name
                )
                logger.info(f"Nuevo usuario creado: {user.uid}") # Aviso de creación de nuevo usuario
            else:
                logger.error("Usuario no encontrado y no es nuevo usuario")
                return jsonify({"success": False, "error": "Usuario no encontrado"}), 404 # Devolver error si el usuario no existe y no es nuevo
        
        # Crear una sesión para el usuario
        session['user_id'] = uid
        session['user_email'] = email
        
        logger.info(f"Sesión creada para {uid}, autenticación exitosa")
        
        # Devolver éxito
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
    
    # Aquí podrías cargar datos del usuario autenticado si lo necesitas
    user_email = session.get('user_email', 'Usuario')
    
    return render_template('principal.html', user_email=user_email)

@app.route('/logout')
def logout(): # Ruta para cerrar sesión
    # Eliminar datos de sesión
    session.pop('user_token', None)
    session.pop('user_id', None)
    session.pop('user_email', None)
    
    logger.info("Usuario desconectado")
    return redirect(url_for('login')) # Redirigir a la página de inicio de sesión

if __name__ == '__main__':
    logger.info("Iniciando aplicación Flask") # Aviso de inicio de aplicación
    app.run(debug=True) # Ejecutar la aplicación Flask en modo de depuración