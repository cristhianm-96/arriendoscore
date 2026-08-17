from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json

app = Flask(__name__)

# 1. CONEXIÓN A GOOGLE SHEETS CON VARIABLES DE ENTORNO
SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Leemos las variables que pusiste en Render
creds_json = {
    "type": "service_account",
    "project_id": os.environ.get('GCP_PROJECT_ID'),
    "private_key_id": os.environ.get('GCP_PRIVATE_KEY_ID'),
    "private_key": os.environ.get('GCP_PRIVATE_KEY').replace('\\n', '\n'),
    "client_email": os.environ.get('GCP_CLIENT_EMAIL'),
    "client_id": os.environ.get('GCP_CLIENT_ID'),
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": os.environ.get('GCP_TOKEN_URI'),
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": os.environ.get('GCP_CLIENT_CERT_URL')
}

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_json, SCOPE)
client = gspread.authorize(creds)
SHEET_ID = os.environ.get('SHEET_ID')


# 2. RUTA PRINCIPAL - BUSCAR USUARIO
@app.route('/', methods=['GET', 'POST'])
def index():
    resultado = None
    if request.method == 'POST':
        email_buscar = request.form['email']
        try:
            sheet = client.open_by_key(SHEET_ID).worksheet("Usuarios")
            cell = sheet.find(email_buscar)
            if cell:
                fila = sheet.row_values(cell.row)
                resultado = {
                    'email': fila[0],
                    'nombre': fila[2],
                    'rol': fila[3],
                    'celular': fila[4],
                    'cupos': fila[5],
                    'estado': fila[6]
                }
            else:
                resultado = "Usuario no encontrado"
        except Exception as e:
            resultado = f"Error: {e}"
    return render_template('index.html', resultado=resultado)


# 3. RUTA PARA MOSTRAR EL FORMULARIO DE REPORTE
@app.route('/reportar')
def form_reporte():
    return render_template('reportar.html')


# 4. RUTA PARA GUARDAR EL REPORTE EN LA PESTAÑA "Reportes"
@app.route('/guardar_reporte', methods=['POST'])
def guardar_reporte():
    try:
        sheet = client.open_by_key(SHEET_ID).worksheet("Reportes")
        
        cc = request.form['cc']
        nombre = request.form['nombre']
        celular = request.form['celular']
        valor = request.form['valor']
        deuda_final = request.form['deuda_final']
        comentario = request.form['comentario']
        quien_reporto = request.form['quien_reporto']
        
        from datetime import datetime
        fecha_inicio = datetime.now().strftime("%Y-%m-%d")
        
        # Valores por defecto según tu estructura
        fecha_fin = ""
        historial_pagos = ""
        daños = "No"
        desalojo = "No"
        
        # Guardar en el mismo orden de tu pestaña Reportes
        sheet.append_row([
            cc, nombre, celular, fecha_inicio, fecha_fin, valor, 
            historial_pagos, deuda_final, daños, desalojo, comentario, quien_reporto
        ])
        
        return "<h2>✅ Reporte Guardado</h2><p>Gracias por alimentar la base de datos de DatoArriendo</p><a href='/'>Volver al Inicio</a>"
        
    except Exception as e:
        return f"<h2>⚠️ Error</h2><p>{e}</p>"


if __name__ == '__main__':
    app.run(debug=True)
