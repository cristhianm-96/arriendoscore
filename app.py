from flask import Flask, render_template, request
import os
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ===== CONFIGURACIÓN GOOGLE SHEETS =====
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

# LEER CREDENCIALES DESDE VARIABLES SEPARADAS - ASI NO FALLA
creds_info = {
    "type": "service_account",
    "project_id": os.environ.get("GCP_PROJECT_ID"),
    "private_key_id": os.environ.get("GCP_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("GCP_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.environ.get("GCP_CLIENT_EMAIL"),
    "client_id": os.environ.get("GCP_CLIENT_ID"),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ.get("GCP_CLIENT_CERT_URL")
}

creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
client = gspread.authorize(creds)

# CAMBIA ESTO POR EL NOMBRE EXACTO DE TU GOOGLE SHEET
SHEET_NAME = "BaseDatos" 
sheet = client.open(SHEET_NAME).sheet1

# ===== RUTAS DE LA APP =====
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        cedula = request.form.get("cedula")
        resultado = buscar_cedula(cedula)
        return render_template("resultado.html", resultado=resultado)
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

def buscar_cedula(cedula):
    try:
        # Busca la cédula en la columna A
        cell = sheet.find(cedula)
        if cell:
            # Obtiene toda la fila de datos
            row = sheet.row_values(cell.row)
            # AJUSTA EL ORDEN SEGÚN TUS COLUMNAS A:G
            datos = {
                "cedula": row[0],
                "nombre": row[1],
                "telefono": row[2],
                "direccion": row[3],
                "estado": row[4],
                "fecha": row[5],
                "notas": row[6]
            }
            return datos
        else:
            return None
    except Exception as e:
        print(f"Error buscando cédula: {e}")
        return None

if __name__ == "__main__":
    app.run(debug=True)
