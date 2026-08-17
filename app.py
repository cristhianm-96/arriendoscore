import os
import json
from flask import Flask, render_template, request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

app = Flask(__name__)

# Configurar Google Sheets
SCOPE = ['https://www.googleapis.com/auth/spreadsheets']
CREDS_JSON = json.loads(os.environ.get('GOOGLE_CREDS_JSON'))
CREDS = Credentials.from_service_account_info(CREDS_JSON, scopes=SCOPE)
SERVICE = build('sheets', 'v4', credentials=CREDS)

# PEGA AQUÍ EL ID DE TU SHEET
SHEET_ID = '1A2B3C4D5E6F7G8H9I0J' # <-- Cámbialo por el ID real de tu Sheet
RANGO = 'Hoja1!A:G' # Asumiendo columnas: Nombre, Cedula, Tel, Direccion, Estado, Fecha, Notas

def buscar_inquilino(cedula):
    result = SERVICE.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=RANGO).execute()
    valores = result.get('values', [])
    for fila in valores[1:]: # Saltamos encabezado
        if len(fila) > 1 and fila[1] == cedula:
            return {
                'nombre': fila[0],
                'cedula': fila[1],
                'telefono': fila[2],
                'direccion': fila[3],
                'estado': fila[4],
                'fecha': fila[5],
                'notas': fila[6]
            }
    return None

@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    if request.method == 'POST':
        cedula = request.form['cedula']
        resultado = buscar_inquilino(cedula)
    return render_template('index.html', resultado=resultado)

@app.route('/admin')
def admin():
    return render_template('admin.html')

if __name__ == '__main__':
    app.run(debug=True)
