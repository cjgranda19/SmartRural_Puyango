def sitio_to_dict(sitio):
    return {
        "_id": str(sitio["_id"]),
        "nombre": sitio["nombre"],
        "descripcion": sitio["descripcion"],
        "lat": sitio["lat"],
        "lon": sitio["lon"],
        "categoria": sitio.get("categoria", ""),
        "estado_via": sitio.get("estado_via", ""),
        "imagen": sitio.get("imagen", ""),
    }

def resena_to_dict(resena):
    return {
        "_id": str(resena["_id"]),
        "sitio_id": str(resena["sitio_id"]),
        "usuario": resena["usuario"],
        "texto": resena["texto"],
        "fecha": resena["fecha"],
        "sentimiento": resena.get("sentimiento", "desconocido")
    }

