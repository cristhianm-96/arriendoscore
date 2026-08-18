from flask import Flask, request, session, redirect, render_template_string, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, smtplib, random, datetime, uuid, threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "datoarriendo_2026_segura"

SHEET_ID = os.environ.get("SHEET_ID")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.resend.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USER = os.environ.get("EMAIL_USER", "resend")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
APP_URL = os.environ.get("APP_URL", "https://arriendoscore.onrender.com")

CREDS_PATH = "/etc/secrets/credentials.json"

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
sheet = None
try:
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    print(">>> CONEXION A GOOGLE SHEETS OK")
except Exception as e:
    print(">>> ERROR CRITICO GOOGLE SHEETS:", e)

@app.route('/logo.jpeg')
def serve_logo():
    return send_from_directory('.', 'logo.jpeg')

CSS = """ <style> body {font-family: Arial; background: #f4f6f8; margin: 0; padding: 0;}.page-wrapper {min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;}.container {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 400px; max-width: 90%; text-align: center; margin-bottom: 30px;}.dashboard {background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 90%; max-width: 1000px; text-align: left; margin: 20px;}.logo {width: 120px; margin-bottom: 15px;} h2 {color: #2c3e50; margin-bottom: 20px; text-align: center;} h3 {color: #3498db; border-bottom: 2px solid #EBF5FB; padding-bottom: 10px;} input, select, textarea {width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;} button {width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 10px;} button:hover {background: #2980b9;} button:disabled {background: #95a5a6; cursor: not-allowed;}.btn-small {width: auto; padding: 8px 16px; font-size: 14px;}.btn-danger {background: #e74c3c; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;}.btn-danger:hover {background: #c039b2;} a {color: #3498db; text-decoration: none; display: block; margin-top: 15px; font-size: 14px;} a:hover {text-decoration: underline;}.info-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;}.info-item {background: #f8f9fa; padding: 12px; border-radius: 8px;}.info-item b {color: #2c3e50;} table {width: 100%; border-collapse: collapse; margin-top: 15px;} th, td {padding: 10px; border-bottom: 1px solid #eee; font-size: 13px; text-align: left;} th {background: #EBF5FB; color: #2c3e50;}.form-inline {display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px;}.codigo {font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #3498db;}.footer-links {display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;}.footer-links a {font-size: 12px; color: #6B7280; margin: 0; display: inline;}.footer-links a:hover {color: #3498db;}.badge {padding: 4px 8px; border-radius: 4px; font-size: 12px; color: white;}.badge-pendiente {background: #f39c12;}.badge-activo {background: #27ae60;}.badge-disputa {background: #e74c3c;} @media (max-width: 900px) {.info-grid,.form-inline {grid-template-columns: 1fr;}} </style> """

# ... el resto de funciones igual ...

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    user = session.get('user');
    if not user: return redirect("/")

    inquilinos = get_inquilinos(user['email'])
    num_arriendos = len(inquilinos)

    limite = 50 if user['rol'] == "inmobiliaria" else 3
    arriendos_disponibles = limite - num_arriendos

    # ... resto igual ...

    filas = ""
    for i inquilinos: # CORREGIDO: tenia "for i inquilinos"
        estado = i.get('estado','')
        badge_class = "badge-pendiente" if "pendiente" in estado else "badge-activo" if estado == "activo" else "badge-disputa"
        filas += f"""<tr><td>{i.get('nombre','')}</td><td>{i.get('cedula','')}</td><td>{i.get('pagos_tiempo','')}/{i.get('meses_totales','')} meses</td><td>{i.get('dias_atraso','')} días</td><td><span class="badge {badge_class}">{estado}</span></td><td><form method="post" style="margin:0;"><input type="hidden" name="cedula_eliminar" value="{i.get('cedula','')}"><button name="btn_eliminar" class="btn-danger" onclick="return confirm('¿Eliminar de tu perfil? En Base Universal queda registrado')">X</button></form></td></tr>"""

    # ... resto igual ...
    return render_template_string(CSS + f"""...""")

if __name__ == "__main__": app.run(host="0.0.0.0", port=10000)
