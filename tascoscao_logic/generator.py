from datetime import datetime

# Catálogo y precios (ejemplo)
CATALOGO = {
    "taza": {
        "blanco": 5.00,
        "negro": 5.50,
    },
    "camiseta": {
        "blanco": 12.00,
        "azul": 12.00,
        "negro": 12.50,
    },
    "bolsa": {
        "natural": 4.00,
        "negra": 4.50,
    },
}

IVA_PORC = 0.21          # 21%
ENVIO_BASE = 3.90        # Envío si no se supera el umbral
ENVIO_GRATIS_DESDE = 30  # Envío gratis desde este subtotal

def _precio_unitario(producto: str, color: str):
    return CATALOGO.get(producto, {}).get(color)

def _normaliza_items(data: dict):
    """
    Acepta dos formatos:
    - { "producto": "...", "color": "...", "cantidad": 2 }
    - { "items": [ { "producto": "...", "color": "...", "cantidad": 2 }, ... ] }
    Devuelve una lista de items homogénea.
    """
    if "items" in data and isinstance(data["items"], list):
        return data["items"]
    # Formato simple -> lo convertimos a lista
    if all(k in data for k in ("producto", "color", "cantidad")):
        return [{
            "producto": data.get("producto"),
            "color": data.get("color"),
            "cantidad": int(data.get("cantidad", 1))
        }]
    return []

def _aplica_cupon(subtotal: float, cupon: str | None) -> tuple[float, dict | None]:
    """
    Aplica cupones simples. Devuelve (descuento, detalle_descuento | None)
    """
    if not cupon:
        return 0.0, None

    cupon = cupon.strip().upper()
    if cupon == "BIENVENIDA10":
        d = round(subtotal * 0.10, 2)
        return d, {"codigo": cupon, "tipo": "porcentaje", "valor": "10%"}
    if cupon == "ENVIOGRATIS":
        # Lo gestionamos en el cálculo del envío (marcamos la intención aquí)
        return 0.0, {"codigo": cupon, "tipo": "envio", "valor": "gratis"}

    return 0.0, {"codigo": cupon, "tipo": "desconocido", "valor": 0}

def process_order(data: dict) -> dict:
    """
    Función principal que usa app.py.
    Recibe un diccionario con el pedido y devuelve un resumen con totales.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    mensajes: list[str] = []
    lineas: list[dict] = []

    items = _normaliza_items(data)
    if not items:
        return {
            "estado": "error",
            "mensaje": "Formato de pedido no válido. Usa 'producto','color','cantidad' o 'items':[...].",
            "timestamp": timestamp
        }

    # Construir líneas
    subtotal = 0.0
    for it in items:
        prod = (it.get("producto") or "").lower()
        color = (it.get("color") or "").lower()
        try:
            qty = int(it.get("cantidad", 1))
        except Exception:
            qty = 1

        p_unit = _precio_unitario(prod, color)
        if p_unit is None:
            mensajes.append(f"Producto/color desconocido: {prod} ({color}).")
            lineas.append({
                "producto": prod,
                "color": color,
                "cantidad": qty,
                "precio_unitario": None,
                "total_linea": 0.0,
                "observacion": "No se encontró en catálogo"
            })
            continue

        total_linea = round(p_unit * qty, 2)
        subtotal = round(subtotal + total_linea, 2)
        lineas.append({
            "producto": prod,
            "color": color,
            "cantidad": qty,
            "precio_unitario": p_unit,
            "total_linea": total_linea
        })

    # Cupón
    cupon = data.get("cupon")
    descuento, info_desc = _aplica_cupon(subtotal, cupon)

    # Envío
    envio = 0.0
    envio_detalle = {"tipo": "estándar", "importe": 0.0}

    # Si cupón es ENVIOGRATIS, siempre 0
    if info_desc and info_desc.get("tipo") == "envio" and info_desc.get("valor") == "gratis":
        envio = 0.0
        envio_detalle["importe"] = 0.0
        envio_detalle["motivo"] = "Cupón de envío gratis"
    else:
        if subtotal >= ENVIO_GRATIS_DESDE:
            envio = 0.0
            envio_detalle["importe"] = 0.0
            envio_detalle["motivo"] = f"Pedido desde {ENVIO_GRATIS_DESDE}€"
        else:
            envio = ENVIO_BASE
            envio_detalle["importe"] = ENVIO_BASE
            envio_detalle["motivo"] = "Tarifa base"

    # IVA sobre (subtotal - descuento)
    base_imponible = max(subtotal - descuento, 0.0)
    iva = round(base_imponible * IVA_PORC, 2)

    total = round(base_imponible + iva + envio, 2)

    resumen = {
        "estado": "procesado",
        "timestamp": timestamp,
        "lineas": lineas,
        "totales": {
            "subtotal": round(subtotal, 2),
            "descuento": round(descuento, 2),
            "iva": iva,
            "envio": round(envio, 2),
            "total": total
        },
        "parametros": {
            "iva_porcentaje": int(IVA_PORC * 100),
            "envio_base": ENVIO_BASE,
            "envio_gratis_desde": ENVIO_GRATIS_DESDE
        }
    }
    if info_desc:
        resumen["cupon"] = info_desc
    if mensajes:
        resumen["mensajes"] = mensajes

    return resumen
