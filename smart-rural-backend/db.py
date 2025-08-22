from pymongo import MongoClient

# Si usas MongoDB Atlas, pega tu cadena de conexión aquí:
MONGO_URI = "mongodb+srv://admin:admin123@cluster0.vjfxsb1.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

client = MongoClient(MONGO_URI)
db = client["smartrural"]

sitios_collection = db["sitios"]
resenas_collection = db["resenas"]
