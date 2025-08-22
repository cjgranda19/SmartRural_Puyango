from flask import Flask
from flask_cors import CORS
from routes.sitios import sitios_bp
from routes.resenas import resenas_bp

app = Flask(__name__)
CORS(app)

# Registrar los endpoints
app.register_blueprint(sitios_bp)
app.register_blueprint(resenas_bp)

@app.route('/')
def index():
    return {"mensaje": "API Smart Rural activa"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

