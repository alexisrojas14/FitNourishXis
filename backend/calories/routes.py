from flask import Blueprint, jsonify, render_template, request, redirect, url_for, session
from utils import get_firebase_uid  # Importar la función desde utils.py
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

calories_bp = Blueprint('calories', __name__)

@calories_bp.route('/calculator', methods=['GET'])
def calculator():
    # Verificar si el usuario está autenticado
    firebaseuid = session.get('user_id')
    if not firebaseuid:
        return redirect(url_for('login'))
    
    return render_template('caloriecalculator.html')

@calories_bp.route('/calculate', methods=['POST'])
def calculate():
    # Verificar si el usuario está autenticado
    firebaseuid = session.get('user_id')
    if not firebaseuid:
        return jsonify({"error": "Usuario no autenticado"}), 401
    
    # Obtener datos del formulario
    data = request.json
    
    try:
        # Extraer datos necesarios
        genero = data.get('genero')
        edad = int(data.get('edad'))
        peso = float(data.get('peso'))  # en kg
        altura = float(data.get('altura'))  # en cm
        nivel_actividad = data.get('nivel_actividad')
        objetivo = data.get('objetivo')
        
        # Calcular TMB (Tasa Metabólica Basal) usando la fórmula de Mifflin-St Jeor
        if genero == 'masculino':
            tmb = 10 * peso + 6.25 * altura - 5 * edad + 5
        elif genero == 'femenino':
            tmb = 10 * peso + 6.25 * altura - 5 * edad - 161
        else:
            # Para "otro", usar un promedio de las fórmulas
            tmb = 10 * peso + 6.25 * altura - 5 * edad - 78
        
        # Aplicar factor de actividad
        factores_actividad = {
            'sedentario': 1.2,
            'ligero': 1.375,
            'moderado': 1.55,
            'activo': 1.725,
            'muy_activo': 1.9
        }
        
        factor = factores_actividad.get(nivel_actividad, 1.2)
        calorias_mantenimiento = tmb * factor
        
        # Ajustar según el objetivo
        ajustes_objetivo = {
            'perder_peso': 0.85,  # Déficit del 15%
            'mantener_peso': 1.0,  # Sin ajuste
            'ganar_masa': 1.1,  # Superávit del 10%
            'mejorar_rendimiento': 1.15,  # Superávit del 15%
            'bienestar': 1.0  # Sin ajuste
        }
        
        ajuste = ajustes_objetivo.get(objetivo, 1.0)
        calorias_diarias = calorias_mantenimiento * ajuste
        
        # Calcular macronutrientes según el objetivo
        if objetivo == 'perder_peso':
            porcentaje_proteinas = 30
            porcentaje_grasas = 30
            porcentaje_carbohidratos = 40
        elif objetivo == 'ganar_masa':
            porcentaje_proteinas = 25
            porcentaje_grasas = 25
            porcentaje_carbohidratos = 50
        elif objetivo == 'mejorar_rendimiento':
            porcentaje_proteinas = 20
            porcentaje_grasas = 20
            porcentaje_carbohidratos = 60
        else:  # mantener_peso o bienestar
            porcentaje_proteinas = 20
            porcentaje_grasas = 30
            porcentaje_carbohidratos = 50
        
        # Calcular gramos de cada macronutriente
        gramos_proteinas = (calorias_diarias * (porcentaje_proteinas / 100)) / 4  # 4 calorías por gramo
        gramos_carbohidratos = (calorias_diarias * (porcentaje_carbohidratos / 100)) / 4  # 4 calorías por gramo
        gramos_grasas = (calorias_diarias * (porcentaje_grasas / 100)) / 9  # 9 calorías por gramo
        
        # Preparar la respuesta
        resultado = {
            "tmb": tmb,
            "calorias_diarias": calorias_diarias,
            "proteinas": gramos_proteinas,
            "carbohidratos": gramos_carbohidratos,
            "grasas": gramos_grasas,
            "porcentaje_proteinas": porcentaje_proteinas,
            "porcentaje_carbohidratos": porcentaje_carbohidratos,
            "porcentaje_grasas": porcentaje_grasas
        }
        
        return jsonify(resultado)
        
    except Exception as e:
        logger.error(f"Error en el cálculo de calorías: {str(e)}")
        return jsonify({"error": f"Error en el cálculo: {str(e)}"}), 500