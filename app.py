from flask import Flask, render_template, request, redirect, url_for, flash
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta_cambiala"

# 1. CONEXIÓN CON GOOGLE SHEETS
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict({
    "type": os.environ["GCP_TYPE"],
    "project_id": os.environ["GCP_PROJECT_ID"],
    "private_key_id": os.environ["GCP_PRIVATE_KEY_ID"],
    "private_key": os.environ["GCP_PRIVATE_KEY"].replace('\\n', '\n'),
    "client_email": os.environ["GCP_CLIENT_EMAIL"],
    "client_id": os.environ["GCP_CLIENT_ID"],
    "auth_uri": os.environ["GCP_AUTH_URI"],
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{os.environ['GCP_CLIENT_EMAIL']}"
}, scope)

client = gspread.authorize(creds)
SHEET_ID = os.environ["SHEET_ID"]

# 2. RUTA PRINCIPAL - BUSCAR USUARIO
@app.route("/", methods=["GET", "POST"])
def index():
    usuario = None
    if request.method == "POST":
        email = request.form["email"]
        try:
            sheet_usuarios = client.open_by_key(SHEET_ID).worksheet("Usuarios")
            data = sheet_usuarios.get_all_records()
            
            for fila in data:
                if fila["Email"] == email:  # OJO: La columna debe llamarse "Email"
                    usuario = fila
                    break
            
            if not usuario:
                flash("Usuario no encontrado", "danger")
                
        except Exception as e:
            flash(f"Error: {e}", "danger")
            
    return render_template("index.html", usuario=usuario)

# 3. RUTA PARA REPORTAR
@app.route("/reportar", methods=["POST"])
def reportar():
    try:
        sheet_reportes = client.open_by_key(SHEET_ID).worksheet("Reportes") # YA CORREGIDO
        
        nuevo_reporte = [
            request.form["email"],
            request.form["direccion"],
            request.form["motivo"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        sheet_reportes.append_row(nuevo_reporte)
        flash("Reporte guardado exitosamente", "success")
        
    except Exception as e:
        flash(f"Error al guardar: {e}", "danger")
        
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
