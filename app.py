from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
import os

app = Flask(__name__)

# 1. LEER LAS 6 VARIABLES DE RENDER
SHEET_ID = os.environ.get('SHEET_ID')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GCP_PRIVATE_KEY_ID = os.environ.get('GCP_PRIVATE_KEY_ID')
GCP_PRIVATE_KEY = os.environ.get('GCP_PRIVATE_KEY_ID') # OJO: Render te lo llama así pero es la llave
GCP_CLIENT_EMAIL = os.environ.get('GCP_CLIENT_EMAIL')
GCP_CLIENT_ID = os.environ.get('GCP_CLIENT_ID')
GCP_CLIENT_CERT_URL = os.environ.get('GCP_CLIENT_CERT_URL')

# 2. ARMAR EL JSON PARA GOOGLE
creds_dict = {
  "type": "service_account",
  "project_id": GCP_PROJECT_ID,
  "private_key_id": GCP_PRIVATE_KEY_ID,
  "private_key": GCP_PRIVATE_KEY.replace('\\n', '\n'), # Esto arregla los \n
  "client_email": GCP_CLIENT_EMAIL,
  "client_id": GCP_CLIENT_ID,
  "client_cert_url": GCP_CLIENT_CERT_URL
}

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(creds_dict, scopes-scopes)
client = gspread.authorize(creds)


# 3. RUTA PRINCIPAL - MUESTRA EL FORMULARIO
@app.route('/')
def home():
    return render_template('index.html')


# 4. RUTA BUSCAR - BUSCA LA CEDULA
@app.route('/buscar', methods=['POST'])
def buscar():
    cedula = request.form['cedula']
    
    try:
        sheet = client.open_by_key(SHEET_ID).sheet1
        cell = sheet.find(cedula)
        
        if cell:
            fila = sheet.row_values(cell.row) # Lee toda la fila
            return f"""
            <h2>✅ Encontrado</h2>
            <p><b>Cédula:</b> {fila[0]}</p>
            <p><b>Nombre:</b> {fila[1]}</p>
            <p><b>Teléfono:</b> {fila[2]}</p>
            <p><b>Estado:</b> {fila[3]}</p>
            <a href='/'>Volver</a>
            """
        else:
            return f"<h2>❌ No encontrado</h2><p>La cédula {cedula} no existe en la base de datos</p><a href='/'>Volver</a>"
            
    except Exception as e:
        return f"<h2>⚠️ Error de conexión</h2><p>{e}</p><a href='/'>Volver</a>"


if __name__ == '__main__':
    app.run()
