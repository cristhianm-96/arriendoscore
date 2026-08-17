from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
import os
import json

app = Flask(__name__)

# 1. CONFIGURAR GOOGLE SHEETS
SHEET_ID = os.environ.get('SHEET_ID')
GCP_CREDENTIALS = os.environ.get('GCP_CREDENTIALS_JSON')

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds_dict = json.loads(GCP_CREDENTIALS)
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)

# 2. RUTA PRINCIPAL - MUESTRA EL FORMULARIO
@app.route('/')
def home():
    return render_template('index.html')


# 3. RUTA BUSCAR - ESTA ES LA QUE FALTABA
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
            return f"<h2>❌ No encontrado</h2><p>La cédula {cedula} no existe</p><a href='/'>Volver</a>"
            
    except Exception as e:
        return f"<h2>⚠️ Error</h2><p>{e}</p><a href='/'>Volver</a>"


if __name__ == '__main__':
    app.run()
