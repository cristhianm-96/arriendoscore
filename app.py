from flask import Flask, render_template, request
import gspread
from google.oauth2.service_account import Credentials
import os

app = Flask(__name__)

# 1. LEER LAS 7 VARIABLES DE RENDER
SHEET_ID = os.environ.get('SHEET_ID')
GCP_PROJECT_ID = os.environ.get('GCP_PROJECT_ID')
GCP_PRIVATE_KEY_ID = os.environ.get('GCP_PRIVATE_KEY_ID')
GCP_PRIVATE_KEY = os.environ.get('GCP_PRIVATE_KEY')
GCP_CLIENT_EMAIL = os.environ.get('GCP_CLIENT_EMAIL')
GCP_CLIENT_ID = os.environ.get('GCP_CLIENT_ID')
GCP_CLIENT_CERT_URL = os.environ.get('GCP_CLIENT_CERT_URL')

# 2. ARMAR EL JSON PARA GOOGLE
creds_dict = {
  "type": "service_account",
  "project_id": GCP_PROJECT_ID,
  "private_key_id": GCP_PRIVATE_KEY_ID,
  "private_key": GCP_PRIVATE_KEY.replace('\\n', '\n'),
  "client_email": GCP_CLIENT_EMAIL,
  "client_id": GCP_CLIENT_ID,
  "client_cert_url": GCP_CLIENT_CERT_URL
}

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
client = gspread.authorize(creds)


# 3. RUTA PRINCIPAL - MUESTRA EL FORMULARIO
@app.route('/')
def home():
    return render_template('index.html')


# 4. RUTA BUSCAR - BUSCA POR EMAIL EN LA PESTAÑA USUARIOS
@app.route('/buscar', methods=['POST'])
def buscar():
    email_buscar = request.form['cedula'] # El form sigue mandando 'cedula'
    
    try:
        # Abre el libro y busca en la pestaña "Usuarios"
        sheet = client.open_by_key(SHEET_ID).worksheet("Usuarios")
        cell = sheet.find(email_buscar)
        
        if cell:
            fila = sheet.row_values(cell.row) # Lee toda la fila
            # A=0 email, B=1 password, C=2 rol, D=3 nombre, E=4 celular, F=5 cupos_totales, G=6 cupos_usados, H=7 estado
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>Resultado</title></head>
            <body style="font-family: Arial; padding: 20px; max-width: 600px; margin: auto;">
                <h2>✅ Usuario Encontrado</h2>
                <p><b>Email:</b> {fila[0]}</p>
                <p><b>Nombre:</b> {fila[3]}</p>
                <p><b>Rol:</b> {fila[2]}</p>
                <p><b>Celular:</b> {fila[4]}</p>
                <p><b>Cupos:</b> {fila[6]} usados de {fila[5]} totales</p>
                <p><b>Estado:</b> {fila[7]}</p>
                <br>
                <a href='/'>Volver a buscar</a>
            </body>
            </html>
            """
        else:
            return f"""
            <!DOCTYPE html>
            <html>
            <head><title>No encontrado</title></head>
            <body style="font-family: Arial; padding: 20px;">
                <h2>❌ No encontrado</h2>
                <p>El email {email_buscar} no existe en la base de datos</p>
                <a href='/'>Volver a buscar</a>
            </body>
            </html>
            """
            
    except Exception as e:
        return f"<h2>⚠️ Error de conexión</h2><p>{e}</p><a href='/'>Volver</a>"


if __name__ == '__main__':
    app.run()
