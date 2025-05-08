def process_order(data):
    # Aquí irá la lógica para generar archivos, ZIP, etc.
    nombre = data.get("nombre", "Desconocido")
    producto = data.get("producto", "sin especificar")
    return {
        "mensaje": f"Pedido de {nombre} para producto: {producto} recibido.",
        "estado": "procesado"
    }
