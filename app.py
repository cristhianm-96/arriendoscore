import os
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, request, render_template

app = Flask(__name__)

# 1. LEER LAS VARIABLES DE ENTORNO DE RENDER
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GCP_PRIVATE_KEY_ID = os.environ.get('GCP_PRIVATE_KEY_ID')
GCP_PRIVATE_KEY = os.environ.get('GCP_PRIVATE_KEY')
GCP_CLIENT_EMAIL = os.environ.get('GCP_CLIENT_EMAIL')
GCP_CLIENT_ID = os.environ.get('GCP_CLIENT_ID')
GCP_CLIENT_CERT_URL = os.environ.get('GCP_CLIENT_CERT_URL')
SHEET_ID = os.environ.get('SHEET_ID')

# 2. CONECTAR CON GOOGLE SHEETS
def conectar_sheets():
    try:
        creds_dict = {
            "type": "service_account",
            "project_id": GCP_PROJECT_ID,
            "private_key_id": GCP_PRIVATE_KEY_ID,
            "private_key": GCP_PRIVATE_KEY,
            "client_email": GCP_CLIENT_EMAIL,
            "client_id": GCP_CLIENT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": GCP_CLIENT_CERT_URL
        }
        scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_ID).sheet1
        return sheet
    except Exception as e:
        print(f"Error conectando con Google: {e}")
        return None

# 3. RUTA PRINCIPAL - BUSCAR POR CEDULA
@app.route('/', methods=['GET', 'POST'])
def index():
    datos = None
    if request.method == 'POST':
        cedula = request.form['cedula']
        sheet = conectar_sheets()
        if sheet:
            try:
                cell = sheet.find(cedula)
                fila = sheet.row_values(cell.row)
                datos = {
                    'cedula': fila[0],
                    'nombre': fila[1],
                    'telefono': fila[2],
                    'estado': fila[3]
                    # Ajusta los índices según las columnas de tu sheet
                }
            except:
                datos = "No encontrado"
    return render_template('index.html', datos=datos)

# 4. RUTA ADMIN
@app.route('/admin')
def admin():
    return render_template('admin.html')


# 5. ESTA ES LA LÍNEA QUE ARREGLA RENDER
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
