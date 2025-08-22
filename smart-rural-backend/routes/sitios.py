"""
Aquí se aplica lógica difusa (ver utils.py)
para estimar el nivel de accesibilidad combinando estado de vía y sentimiento de reseñas.
"""
from flask import Blueprint, jsonify
from db import sitios_collection, resenas_collection
from models import sitio_to_dict
from utils import estimar_accesibilidad

sitios_bp = Blueprint('sitios', __name__)

@sitios_bp.route('/sitios', methods=['GET'])
def obtener_sitios():
    sitios = list(sitios_collection.find())
    sitios_con_accesibilidad = []

    for sitio in sitios:
        sitio_dict = sitio_to_dict(sitio)

        # Obtener reseñas del sitio
        resenas = list(resenas_collection.find({"sitio_id": sitio["_id"]}))
        total = len(resenas)
        positivas = sum(1 for r in resenas if r.get("sentimiento") == "positivo")
        porcentaje_positivas = positivas / total if total > 0 else 0.5

        # Aplicar lógica difusa
        accesibilidad = estimar_accesibilidad(sitio.get("estado_via", "regular"), porcentaje_positivas)

        sitio_dict["accesibilidad"] = accesibilidad
        sitios_con_accesibilidad.append(sitio_dict)

    return jsonify(sitios_con_accesibilidad)
