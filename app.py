import os
import json
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambia-esta-clave")

# ---------------------------------------------------------------------------
# Configuración de Google Sheets
# ---------------------------------------------------------------------------
# En Render, guarda el JSON de la cuenta de servicio completo como una
# variable de entorno llamada GOOGLE_CREDENTIALS_JSON (pega el contenido
# del archivo .json tal cual).
#
# El archivo de Google Sheets se llama "Usuarios" y dentro tiene 2 pestañas:
#   - Usuarios: email, nombre, rol, celular, cupos, estado, direccion
#   - Reportes: email, direccion, motivo, fecha
#
# IMPORTANTE: recuerda compartir el Sheet con el email de la cuenta de
# servicio (client_email dentro del JSON) para que pueda leer/escribir.

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

NOMBRE_SPREADSHEET = "Usuarios"


def get_client():
    creds_json = os.environ.get("GOOGLE_CREDENTIALS_JSON")
    if not creds_json:
        raise RuntimeError("Falta la variable de entorno GOOGLE_CREDENTIALS_JSON")
    creds_dict = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)


def get_spreadsheet():
    client = get_client()
    return client.open(NOMBRE_SPREADSHEET)


def get_sheet(nombre_pestana):
    return get_spreadsheet().worksheet(nombre_pestana)


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def buscar_usuario_por_email(email):
    """Busca un usuario en la pestaña 'Usuarios' por email y devuelve un dict."""
    ws = get_sheet("Usuarios")
    registros = ws.get_all_records()  # usa la primera fila como encabezados
    email = (email or "").strip().lower()

    for row in registros:
        if str(row.get("email", "")).strip().lower() == email:
            return row
    return None


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html", usuario=None, email_buscado=None)


@app.route("/buscar", methods=["POST"])
def buscar():
    email = request.form.get("email", "").strip()

    usuario = None
    try:
        usuario = buscar_usuario_por_email(email)
    except Exception as e:
        flash(f"Error al consultar la hoja: {e}")

    if not usuario:
        flash("No se encontró ningún usuario con ese email.")

    return render_template("index.html", usuario=usuario, email_buscado=email)


@app.route("/reportar", methods=["POST"])
def reportar():
    email = request.form.get("email", "").strip()
    direccion = request.form.get("direccion", "").strip()
    motivo = request.form.get("motivo", "").strip()

    if not email or not motivo:
        flash("Faltan datos para registrar el reporte.")
        return redirect(url_for("index"))

    fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        ws = get_sheet("Reportes")
        # Orden de columnas en la pestaña Reportes: email, direccion, motivo, fecha
        ws.append_row([email, direccion, motivo, fecha_hoy],
                      value_input_option="USER_ENTERED")
        flash("Novedad reportada correctamente.")
    except Exception as e:
        flash(f"Error al guardar el reporte: {e}")

    # Volvemos a mostrar el usuario buscado, como si acabaras de encontrarlo
    usuario = None
    try:
        usuario = buscar_usuario_por_email(email)
    except Exception:
        pass

    return render_template("index.html", usuario=usuario, email_buscado=email)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
