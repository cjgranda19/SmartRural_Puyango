"""
Lógica difusa con scikit-fuzzy para estimar accesibilidad.
Combina estado de la vía y sentimiento agregado de reseñas
mediante funciones de membresía y reglas difusas.
"""
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Definición de variables difusas (antecedentes y consecuente)
estado_via = ctrl.Antecedent(np.arange(0, 11, 1), 'estado_via')
sentimiento = ctrl.Antecedent(np.arange(0, 11, 1), 'sentimiento')
accesibilidad = ctrl.Consequent(np.arange(0, 11, 1), 'accesibilidad')

# Funciones de membresía
estado_via['malo'] = fuzz.trimf(estado_via.universe, [0, 0, 4])
estado_via['regular'] = fuzz.trimf(estado_via.universe, [2, 5, 8])
estado_via['bueno'] = fuzz.trimf(estado_via.universe, [6, 10, 10])

sentimiento['negativo'] = fuzz.trimf(sentimiento.universe, [0, 0, 4])
sentimiento['neutral'] = fuzz.trimf(sentimiento.universe, [2, 5, 8])
sentimiento['positivo'] = fuzz.trimf(sentimiento.universe, [6, 10, 10])

accesibilidad['baja'] = fuzz.trimf(accesibilidad.universe, [0, 0, 4])
accesibilidad['media'] = fuzz.trimf(accesibilidad.universe, [3, 5, 7])
accesibilidad['alta'] = fuzz.trimf(accesibilidad.universe, [6, 10, 10])

# Reglas difusas (base de conocimiento)
regla1 = ctrl.Rule(estado_via['bueno'] & sentimiento['positivo'], accesibilidad['alta'])
regla2 = ctrl.Rule(estado_via['regular'] & sentimiento['neutral'], accesibilidad['media'])
regla3 = ctrl.Rule(estado_via['malo'] | sentimiento['negativo'], accesibilidad['baja'])
regla4 = ctrl.Rule(estado_via['bueno'] & sentimiento['neutral'], accesibilidad['media'])
regla5 = ctrl.Rule(estado_via['regular'] & sentimiento['positivo'], accesibilidad['media'])
regla6 = ctrl.Rule(estado_via['malo'] & sentimiento['positivo'], accesibilidad['media'])

# Sistema de control difuso
sistema_ctrl = ctrl.ControlSystem([regla1, regla2, regla3, regla4, regla5, regla6])
sistema = ctrl.ControlSystemSimulation(sistema_ctrl)

def estimar_accesibilidad(estado, sentimiento_score):
    """
    Evalúa el sistema difuso y devuelve una etiqueta textual de accesibilidad
    a partir del estado de la vía ('malo', 'regular', 'bueno') y un score de
    sentimiento en rango 0–10 (derivado de opiniones positivas).
    """
    # Convertimos estado_via (texto) a valor numérico
    estado_map = {'malo': 2, 'regular': 5, 'bueno': 8}
    estado_val = estado_map.get(estado, 5)

    # Entrada al sistema difuso
    sistema.input['estado_via'] = estado_val
    sistema.input['sentimiento'] = sentimiento_score  # 0 a 10

    sistema.compute()
    salida = sistema.output['accesibilidad']

    # Clasificación textual
    if salida < 4:
        return "Baja"
    elif salida < 7:
        return "Media"
    else:
        return "Alta"
