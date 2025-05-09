from flask import Flask, request, jsonify
from tascoscao_logic.generator import process_order

app = Flask(__name__)

@app.route("/")
def home():
    return "Tascoscao Backend
    Online"

@app.route("/procesar_pedido", methods=["POST"])
def procesar_pedido():
    data = request.json
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    resultado = process_order(data)
    return jsonify(resultado)

if __name__ == "__main__":
app.run(host="0.0.0.0", port=10000)  
