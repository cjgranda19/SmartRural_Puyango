from pymongo import MongoClient

# Conexión a MongoDB Atlas
MONGO_URI = "mongodb+srv://admin:admin123@cluster0.vjfxsb1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["smartrural"]
sitios_collection = db["sitios"]

nuevos_sitios = [
    {
        "nombre": "Finca Integral El Balsal",
        "descripcion": "Granja orgánica enfocada en sostenibilidad, agroturismo y educación ambiental.",
        "lat": -4.043524,
        "lon": -80.033311,
        "categoria": "finca orgánica",
        "estado_via": "regular"
    },
    {
        "nombre": "Complejo Turístico - Aguas Sulfurosas de Arenal",
        "descripcion": "Complejo natural con piscinas termales, senderos y servicios turísticos en El Arenal.",
        "lat": -4.020274,
        "lon": -80.057709,
        "categoria": "aguas termales",
        "estado_via": "bueno"
    },
    {
        "nombre": "Museo Vivo de Abejas Nativas",
        "descripcion": "Espacio de conservación y educación sobre las abejas nativas sin aguijón, único en la región sur.",
        "lat": -4.014113,
        "lon": -80.053947,
        "categoria": "cultural",
        "estado_via": "excelente"
    }
]

# Insertar los datos
sitios_collection.insert_many(nuevos_sitios)
print("✅ Sitios Plus Code insertados correctamente.")
