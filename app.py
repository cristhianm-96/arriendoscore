import os
import json
from flask import Flask, render_template, request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# 1. CONEXIÓN CON GOOGLE SHEETS
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
creds_json_str = os.environ.get('GOOGLE_CREDS_JSON')
creds_json_str = creds_json_str.replace('\\n', '\n') # Arregla los saltos de línea de la llave
CREDS_JSON = json.loads(creds_json_str)
CREDS = Credentials.from_service_account_info(CREDS_JSON, scopes=SCOPE)
SERVICE = build('sheets', 'v4', credentials=CREDS)

# 2. DATOS DE TU SHEET
SHEET_ID = os.environ.get('SHEET_ID') # Lee el ID desde Render
RANGO = 'Hoja1!A:G' # Cambia "Hoja1" si tu pestaña se llama diferente. A=cedula, B=nombre, C=tel, D=direccion, E=estado, F=fecha, G=notas

# 3. RUTAS DE LA WEB
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/buscar', methods=['POST'])
def buscar():
    cedula_buscar = request.form['cedula']
    
    try:
        # Lee todos los datos de la hoja
        result = SERVICE.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGO).execute()
        valores = result.get('values', [])
        
        datos = None
        # Recorre fila por fila buscando la cédula. Empieza en 1 para saltar encabezados
        for fila in valores[1:]: 
            if len(fila) > 0 and fila[0] == cedula_buscar:
                datos = {
                    'cedula': fila[0],
                    'nombre': fila[1] if len(fila) > 1 else '',
                    'telefono': fila[2] if len(fila) > 2 else '',
                    'direccion': fila[3] if len(fila) > 3 else '',
                    'estado': fila[4] if len(fila) > 4 else '',
                    'fecha': fila[5] if len(fila) > 5 else '',
                    'notas': fila[6] if len(fila) > 6 else ''
                }
                break
        
        return render_template('resultado.html', resultado=datos)
        
    except Exception as e:
        return f"Error al conectar con Google: {e}"

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
