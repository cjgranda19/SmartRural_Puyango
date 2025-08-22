"""
Este módulo aplica:
- PLN (Procesamiento de Lenguaje Natural) con TextBlob + traducción (googletrans)
    para analizar el sentimiento de las reseñas y clasificarlas en positivo/neutral/negativo.
- Una aproximación sencilla de lógica difusa (promedio de variables) para estimar accesibilidad.
    Para un modelo difuso completo con reglas y funciones de membresía, ver utils/accesibilidad.py.
"""

from textblob import TextBlob

def generar_recomendacion_inteligente(porcentajes, accesibilidad, total_resenas):
    """
    Genera una recomendación detallada basada en los porcentajes de sentimientos y accesibilidad
    """
    positivo = porcentajes["positivo"]
    negativo = porcentajes["negativo"]
    neutral = porcentajes["neutral"]
    
    # Determinar confiabilidad basada en número de reseñas
    if total_resenas >= 20:
        confiabilidad = "alta"
    elif total_resenas >= 10:
        confiabilidad = "media"
    elif total_resenas >= 5:
        confiabilidad = "baja"
    else:
        confiabilidad = "muy baja"
    
    # Construir recomendación
    recomendacion = []
    
    # Análisis principal
    if positivo >= 80:
        recomendacion.append("✅ EXCELENTE DESTINO: Este lugar tiene opiniones excepcionales.")
        recomendacion.append("🎯 Muy seguro para visitar con familia y amigos.")
    elif positivo >= 60:
        recomendacion.append("✅ BUEN DESTINO: La mayoría de visitantes tuvieron experiencias positivas.")
        recomendacion.append("👍 Recomendado para la mayoría de tipos de viajeros.")
    elif positivo >= 40:
        recomendacion.append("⚠️ DESTINO REGULAR: Experiencias mixtas reportadas.")
        recomendacion.append("🤔 Considera los riesgos antes de visitar.")
    elif negativo >= 60:
        recomendacion.append("❌ DESTINO PROBLEMÁTICO: Múltiples experiencias negativas.")
        recomendacion.append("🚫 No recomendado especialmente para familias.")
    else:
        recomendacion.append("⚠️ INFORMACIÓN INSUFICIENTE: Pocas opiniones disponibles.")
        recomendacion.append("🔍 Investiga más antes de tu visita.")
    
    # Análisis de accesibilidad
    if accesibilidad == "alta":
        recomendacion.append("🚗 ACCESO FÁCIL: Carreteras en buen estado, accesible para todo tipo de vehículos.")
    elif accesibilidad == "media":
        recomendacion.append("🚙 ACCESO MODERADO: Se recomienda vehículo con buena altura, carretera regular.")
    else:
        recomendacion.append("🚜 ACCESO DIFÍCIL: Solo vehículos 4x4 o caminata, carretera en mal estado.")
    
    # Recomendaciones específicas
    if negativo >= 30:
        recomendacion.append("⚠️ PRECAUCIONES: Algunos visitantes reportaron problemas. Lee las reseñas negativas.")
    
    if neutral >= 40:
        recomendacion.append("📊 Las opiniones están divididas - la experiencia puede variar mucho.")
    
    # Nivel de confiabilidad
    if confiabilidad == "muy baja":
        recomendacion.append(f"📈 Solo {total_resenas} reseña(s) disponible(s). Toma esta información con cautela.")
    elif confiabilidad == "baja":
        recomendacion.append(f"📈 Basado en {total_resenas} reseñas. Se necesitan más opiniones para mayor precisión.")
    elif confiabilidad == "media":
        recomendacion.append(f"📈 Basado en {total_resenas} reseñas. Información moderadamente confiable.")
    else:
        recomendacion.append(f"📈 Basado en {total_resenas} reseñas. Información muy confiable.")
    
    return " | ".join(recomendacion)
# LÓGICA DIFUSA APLICADA
def estimar_accesibilidad(estado_via: str, opiniones_positivas: float) -> str:
    """
    LÓGICA DIFUSA (versión simplificada):
    Combina el estado de la vía (malo/regular/bueno) y la fracción de opiniones positivas (0–1)
    para estimar un nivel de accesibilidad: 'alta' | 'media' | 'baja'.

    Nota: Esta es una aproximación ligera (promedio). El modelo difuso formal con scikit-fuzzy
    está implementado en utils/accesibilidad.py y se usa cuando se requiere mayor detalle.
    """
    if estado_via == "bueno":
        via_valor = 1.0
    elif estado_via == "regular":
        via_valor = 0.5
    else:  # malo
        via_valor = 0.0

    promedio = (via_valor + opiniones_positivas) / 2

    if promedio >= 0.7:
        return "alta"
    elif promedio >= 0.4:
        return "media"
    else:
        return "baja"


# Análisis de sentimiento usando PLN
def analizar_sentimiento(texto):
    """
    PLN: Analiza el sentimiento del texto de la reseña.
    - Traduce el texto a inglés para mejorar la precisión de TextBlob.
    - Usa TextBlob.sentiment.polarity para clasificar en 'positivo' | 'neutral' | 'negativo'.
    """
    # Traducción opcional: intentar usar googletrans si está disponible
    try:
        from googletrans import Translator  # import local para evitar warning del linter si no está instalado
        _translator = Translator()
        texto_en = _translator.translate(texto, dest='en').text
    except Exception:
        # Si no está googletrans o falla la traducción, usamos el texto original
        texto_en = texto

    polaridad = TextBlob(texto_en).sentiment.polarity

    if polaridad > 0.1:
        return 'positivo'
    elif polaridad < -0.1:
        return 'negativo'
    else:
        return 'neutral'

