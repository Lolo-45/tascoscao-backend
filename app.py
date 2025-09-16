from flask import Flask, request, jsonify
from tascoscao_logic.generator import process_order  # <- import correcto

app = Flask(__name__)

@app.route("/")
def home():
    return "Tascoscao Backend Online"

@app.route("/procesar_pedido", methods=["POST"])
def procesar_pedido():
    # Asegura que recibimos JSON
    if not request.is_json:
        return jsonify({"error": "El cuerpo debe ser JSON"}), 400

    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    try:
        resultado = process_order(data)
        return jsonify(resultado), 200
    except Exception as e:
        # Evita que el servidor caiga si algo falla dentro de process_order
        return jsonify({"error": str(e)}), 500


# Render usará gunicorn con app:app, pero esto permite ejecutar localmente
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=False)
