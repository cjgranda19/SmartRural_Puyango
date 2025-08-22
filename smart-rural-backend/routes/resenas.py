"""
Este endpoint usa PLN (TextBlob) para analizar el sentimiento de cada reseña.
También calcula un resumen y recomienda en base a sentimientos y accesibilidad.
Además infiere: rango de edad, accesibilidad para discapacidad, meses
recomendados, confianza de datos, tendencia mensual, tags, alertas y consejos.
"""
from flask import Blueprint, request, jsonify
from db import resenas_collection
from models import resena_to_dict
from bson import ObjectId
from textblob import TextBlob
from datetime import datetime, timedelta
from utils import analizar_sentimiento, generar_recomendacion_inteligente
from utils import estimar_accesibilidad
from db import sitios_collection

# ------------------- Helpers locales (rutas no cambian) -------------------

import re
from collections import defaultdict, Counter
from math import ceil

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril",
    5: "mayo", 6: "junio", 7: "julio", 8: "agosto",
    9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"
}
MESES_CORTO = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic"
}

def _tokenizar(texto):
    """Tokenización simple para matching por palabra."""
    return re.findall(r"[a-záéíóúñü]+", (texto or "").lower())

def _to_float01(v):
    """Normaliza 'alta/media/baja' o números a rango [0,1]."""
    if isinstance(v, (int, float)):
        try:
            return max(0.0, min(1.0, float(v)))
        except Exception:
            return 0.5
    if isinstance(v, str):
        s = v.strip().lower()
        if s == "alta": return 0.85
        if s == "media": return 0.6
        if s == "baja": return 0.3
        try:
            f = float(s)
            return max(0.0, min(1.0, f))
        except Exception:
            return 0.5
    return 0.5

def _acc_texto(v_float):
    if v_float >= 0.7: return "alta"
    if v_float >= 0.4: return "media"
    return "baja"

def _inferir_edad(resenas_textos):
    """Heurística por lexicones para rango de edad sugerido."""
    kw_child_pos = {"niño","niños","infantil","familia","familiar","hijos","pequeños","carriola","cochecito"}
    kw_child_neg = {"noapto","peligroso","riesgoso"}
    kw_senior_pos = {"adultos","mayores","tercera","edad","plano","tranquilo","corto","descanso"}
    kw_senior_neg = {"escalera","escaleras","empinado","resbaloso","barro","trekking","subida","caminata","largo"}
    kw_aventura   = {"aventura","adrenalina","rápel","rapel","rafting","escalada"}

    scp = scn = ssp = ssn = sav = 0
    for t in resenas_textos:
        toks = _tokenizar(t)
        joined = "".join(toks)  # "no apto" ~ "noapto"
        scp += sum(w in kw_child_pos for w in toks)
        scn += sum(w in kw_child_neg for w in [joined])
        ssp += sum(w in kw_senior_pos for w in toks)
        ssn += sum(w in kw_senior_neg for w in toks)
        sav += sum(w in kw_aventura   for w in toks)

    niños_ok  = scp > scn
    senior_ok = ssp >= ssn // 2
    if niños_ok and senior_ok:   return "todas las edades"
    if niños_ok and not senior_ok: return "niños (6+) y adultos; no ideal para adultos mayores"
    if not niños_ok and senior_ok: return "adultos y adultos mayores"
    if sav: return "adolescentes y adultos (12+)"
    return "adolescentes y adultos (12+)"

def _inferir_discapacidad(resenas_textos, nivel_accesibilidad):
    """Combina valor difuso + pistas en texto."""
    a = _to_float01(nivel_accesibilidad)
    kw_pos = {"rampa","rampas","accesible","accesibilidad","silla","ruedas","estacionamiento","plano"}
    kw_neg = {"escalera","escaleras","barro","piedras","irregular","lodoso","estrecho","empinado","resbaloso"}

    pos = neg = 0
    for t in resenas_textos:
        toks = set(_tokenizar(t))
        pos += len(kw_pos & toks)
        neg += len(kw_neg & toks)

    if a >= 0.7 and neg == 0: return "apto para personas con discapacidad"
    if 0.4 <= a < 0.7 or (pos > 0 and neg > 0): return "apto para personas discapacitadas con apoyo"
    return "no recomendado para personas discapacitadas"

def _parse_fecha(fecha):
    """Soporta datetime, ISO string o dict tipo {'$date': ...}."""
    if isinstance(fecha, datetime):
        return fecha
    if isinstance(fecha, dict) and "$date" in fecha:
        try:
            return datetime.fromisoformat(str(fecha["$date"]).replace("Z", "+00:00"))
        except Exception:
            return None
    try:
        return datetime.fromisoformat(str(fecha))
    except Exception:
        return None

def _mejores_meses(resenas):
    """Top 3 meses por % positivo (con mínimos por mes)."""
    if not resenas:
        return {"mejores_meses": [], "detalle_meses": []}

    por_mes = defaultdict(lambda: {"pos": 0, "tot": 0})
    for r in resenas:
        f = _parse_fecha(r.get("fecha"))
        if not f: continue
        m = f.month
        por_mes[m]["tot"] += 1
        if (r.get("sentimiento") or "neutral") == "positivo":
            por_mes[m]["pos"] += 1

    total = len(resenas)
    min_mes = max(2, ceil(0.1 * total))  # >=2 o 10%

    cand = []
    for m, st in por_mes.items():
        if st["tot"] >= min_mes:
            pct = round(100 * st["pos"] / st["tot"], 2)
            cand.append((m, pct, st["tot"]))

    if not cand:
        return {"mejores_meses": [], "detalle_meses": []}

    cand.sort(key=lambda x: (x[1], x[2]), reverse=True)
    top = [MESES_ES[m] for (m, _, _) in cand[:3]]
    detalle = [{"mes": MESES_ES[m], "positividad": pct, "n": n} for (m, pct, n) in cand]
    return {"mejores_meses": top, "detalle_meses": detalle}

def _tendencia_12m(resenas):
    """Serie de 12 meses (mes corto, % positivo, n)."""
    hoy = datetime.now()
    # mapa (año, mes) -> pos/tot
    por_mes = defaultdict(lambda: {"pos": 0, "tot": 0})
    for r in resenas:
        f = _parse_fecha(r.get("fecha"))
        if not f: continue
        ym = (f.year, f.month)
        por_mes[ym]["tot"] += 1
        if (r.get("sentimiento") or "neutral") == "positivo":
            por_mes[ym]["pos"] += 1

    serie = []
    for i in range(11, -1, -1):
        ref = hoy.replace(day=15) - timedelta(days=30*i)
        ym = (ref.year, ref.month)
        st = por_mes.get(ym, {"pos":0,"tot":0})
        pct = round(100*st["pos"]/st["tot"],2) if st["tot"]>0 else 0.0
        serie.append({"mes": MESES_CORTO[ym[1]], "pct_positivo": pct, "n": st["tot"]})
    return serie

def _confianza(resenas):
    """Nivel de confianza segun volumen y frescura."""
    total = len(resenas)
    hace_90 = datetime.now() - timedelta(days=90)
    n_90 = 0
    for r in resenas:
        f = _parse_fecha(r.get("fecha"))
        if f and f >= hace_90:
            n_90 += 1
    if total >= 15 and n_90 >= 3:
        nivel = "alta"
    elif total >= 6 and n_90 >= 1:
        nivel = "media"
    else:
        nivel = "baja"
    return {"nivel": nivel, "n_total": total, "n_ultimos_90d": n_90}

def _tags(resenas_textos):
    """Extrae tags por lexicon básico y devuelve top 6."""
    lex = {
        "familia": {"familia","familiar","niño","niños","hijos","infantil"},
        "4x4": {"4x4","camioneta","pickup","alto","todo","terreno"},
        "barro": {"barro","lodoso","lodo","resbaloso"},
        "naturaleza": {"naturaleza","bosque","río","rio","cascada","laguna","mirador","sendero"},
        "seguro": {"seguro","tranquilo","calmado"},
        "aventura": {"aventura","adrenalina","rapel","rápel","rafting","escalada"},
        "camping": {"camping","acampar","tienda"},
        "fotografía": {"foto","fotos","fotografía","fotografias"},
        "mascotas": {"mascota","perro","perros","petfriendly","pet"},
        "servicios": {"baños","baño","tienda","kiosko","restaurante","parqueo","estacionamiento"},
    }
    score = Counter()
    for t in resenas_textos:
        toks = set(_tokenizar(t))
        for tag, kws in lex.items():
            if toks & kws:
                score[tag] += 1
    # top 6 por frecuencia
    return [t for (t, _) in score.most_common(6)]

def _alertas(resenas_textos):
    """Genera alertas si ciertos términos aparecen con frecuencia."""
    neg_terreno = {"escalera","escaleras","empinado","resbaloso","barro","lodoso","piedras","estrecho"}
    inseg = {"robo","inseguro","peligroso","asalto","ladrones"}
    agua = {"crecida","crece","desborda","corriente","caudaloso"}

    c_terreno = c_inseg = c_agua = 0
    for t in resenas_textos:
        toks = set(_tokenizar(t))
        if toks & neg_terreno: c_terreno += 1
        if toks & inseg: c_inseg += 1
        if toks & agua: c_agua += 1

    total = max(1, len(resenas_textos))
    out = []
    if c_terreno/total >= 0.15 or c_terreno >= 3:
        out.append("⚠️ Muchas menciones de terreno difícil (escaleras/empinado/barro).")
    if c_inseg/total >= 0.1 or c_inseg >= 2:
        out.append("⚠️ Algunas reseñas señalan problemas de seguridad.")
    if c_agua/total >= 0.1 or c_agua >= 2:
        out.append("⚠️ Atención a crecida de ríos o corrientes fuertes en ciertas épocas.")
    return out

def _consejos(tags_list, discapacidad, mejores_meses):
    """Consejos prácticos según señales detectadas."""
    tips = []
    if "4x4" in tags_list: tips.append("Usa vehículo alto o 4x4 si está disponible.")
    if "barro" in tags_list: tips.append("Lleva botas y ropa de cambio si llueve.")
    if "familia" in tags_list: tips.append("Buen lugar para ir en familia; lleva snacks y protector solar.")
    if "camping" in tags_list: tips.append("Si acampas, lleva linterna y bolsa para residuos.")
    if discapacidad == "apto con apoyo": tips.append("Para silla de ruedas, considera acompañante por tramos irregulares.")
    if mejores_meses: tips.append(f"Mejor época: {', '.join(mejores_meses)}.")
    return tips[:6]

# ------------------- Blueprint y endpoints (SIN CAMBIOS DE RUTA) -------------------

resenas_bp = Blueprint('resenas', __name__)

@resenas_bp.route('/resenas', methods=['POST'])
def crear_resena():
    data = request.json or {}

    texto = data.get('texto', '')
    sentimiento_str = analizar_sentimiento(texto)

    resena = {
        "sitio_id": ObjectId(data["sitio_id"]),
        "usuario": data.get("usuario","Anónimo"),
        "texto": texto,
        "fecha": datetime.now(),
        "sentimiento": sentimiento_str
    }

    resultado = resenas_collection.insert_one(resena)
    resena["_id"] = resultado.inserted_id
    return jsonify(resena_to_dict(resena)), 201


@resenas_bp.route('/resenas/<sitio_id>', methods=['GET'])
def obtener_resenas_por_sitio(sitio_id):
    try:
        oid = ObjectId(sitio_id)
    except Exception:
        return jsonify([]), 200
    resenas = list(resenas_collection.find({"sitio_id": oid}))
    resenas_dict = [resena_to_dict(r) for r in resenas]
    return jsonify(resenas_dict), 200


@resenas_bp.route('/resumen/<sitio_id>', methods=['GET'])
def resumen_resenas(sitio_id):
    # Carga segura de reseñas
    try:
        filtro = {"sitio_id": ObjectId(sitio_id)}
    except Exception:
        return jsonify({
            "total": 0, "porcentajes": {"positivo": 0, "neutral": 0, "negativo": 0},
            "conclusion": "ID de sitio no válido.",
            "recomendacion": "Verifica el identificador del sitio.",
            "accesibilidad": "desconocida",
            "edad_sugerida": "sin datos", "discapacidad": "sin datos",
            "mejores_meses": [], "detalle_meses": [],
            "confianza": {"nivel":"baja","n_total":0,"n_ultimos_90d":0},
            "tendencia": [], "tags": [], "alertas": [], "consejos": []
        }), 200

    resenas = list(resenas_collection.find(filtro))
    total = len(resenas)

    if total == 0:
        return jsonify({
            "total": 0,
            "porcentajes": {"positivo": 0, "neutral": 0, "negativo": 0},
            "conclusion": "Este sitio aún no tiene reseñas.",
            "recomendacion": "Aún no hay suficientes datos para recomendar.",
            "accesibilidad": "desconocida",
            "edad_sugerida": "sin datos",
            "discapacidad": "sin datos",
            "mejores_meses": [],
            "detalle_meses": [],
            "confianza": {"nivel":"baja","n_total":0,"n_ultimos_90d":0},
            "tendencia": [], "tags": [], "alertas": [], "consejos": []
        }), 200

    # Conteo de sentimientos
    sentimientos = [(r.get('sentimiento') or 'neutral') for r in resenas]
    conteo = Counter(sentimientos)
    porcentajes = {
        "positivo": round((conteo.get("positivo", 0) / total) * 100, 2),
        "neutral":  round((conteo.get("neutral",  0) / total) * 100, 2),
        "negativo": round((conteo.get("negativo", 0) / total) * 100, 2)
    }

    # Estado de vía
    sitio = sitios_collection.find_one({"_id": ObjectId(sitio_id)})
    estado_via = (sitio or {}).get("estado_via", "regular")

    # Accesibilidad (normalizada a 0..1) + texto + explicación
    opiniones_positivas_valor = porcentajes["positivo"] / 100.0
    acc_val = _to_float01(estimAR := estimar_accesibilidad(estado_via, opiniones_positivas_valor))
    acc_txt = _acc_texto(acc_val)

    # Heurísticas adicionales
    textos = [(r.get("texto") or "") for r in resenas]
    edad_sugerida = _inferir_edad(textos)
    discapacidad = _inferir_discapacidad(textos, acc_val)
    meses_info = _mejores_meses(resenas)

    # Datos extendidos
    tendencia = _tendencia_12m(resenas)
    confianza = _confianza(resenas)
    tags = _tags(textos)
    alertas = _alertas(textos)
    consejos = _consejos(tags, discapacidad, meses_info["mejores_meses"])

    # Recomendación AI-like
    recomendacion = generar_recomendacion_inteligente(porcentajes, acc_val, total)
    
    # Conclusión
    if porcentajes["positivo"] >= 70:
        conclusion = "🔵 Altamente recomendado - Excelentes opiniones de visitantes"
    elif porcentajes["positivo"] >= 50:
        conclusion = "🟢 Recomendado - Buenas experiencias reportadas"
    elif porcentajes["negativo"] >= 60:
        conclusion = "🔴 No recomendado - Múltiples experiencias negativas"
    elif porcentajes["negativo"] >= 40:
        conclusion = "🟡 Visitar con precaución - Experiencias mixtas con tendencia negativa"
    else:
        conclusion = "🟡 Recomendado con reservas - Opiniones variadas"

    return jsonify({
        "total": total,
        "porcentajes": porcentajes,
        "conclusion": conclusion,
        "recomendacion": recomendacion,
        "accesibilidad": acc_val,                 # num 0..1 (para UI)
        "accesibilidad_texto": acc_txt,           # opcional (comodín)
        "edad_sugerida": edad_sugerida,
        "discapacidad": discapacidad,
        "mejores_meses": meses_info["mejores_meses"],
        "detalle_meses": meses_info["detalle_meses"],
        "tendencia": tendencia,
        "confianza": confianza,
        "tags": tags,
        "alertas": alertas,
        "consejos": consejos
    }), 200
