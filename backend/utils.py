from flask import session
import logging

logger = logging.getLogger(__name__)

def get_firebase_uid():
    """
    Obtiene el UID de Firebase del usuario autenticado.
    """
    try:
        if 'user_id' in session:
            return session['user_id']  # Retornar el UID almacenado en la sesión
        else:
            logger.warning("Intento de obtener UID sin autenticación")
            return None
    except Exception as e:
        logger.error(f"Error al obtener el UID de Firebase: {e}")
        return None