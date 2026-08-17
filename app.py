from flask import Flask, request, session, redirect, render_template_string
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import base64
import tempfile
from datetime import datetime

app = Flask(__name__)
app.secret_key = "datoarriendo_2026_segura"
print(">>> DATOARRIENDO INICIANDO...")

SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDENTIALS_B64 = os.environ.get("GOOGLE_CREDENTIALS_B64")

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
sheet = None
try:
    print(">>> LARGO B64:", len(GOOGLE_CREDENTIALS_B64))
    print(">>> DECODIFICANDO CREDENCIALES...")
    
    # Claude 4 Fix: Guardar en archivo temporal
    creds_json_str = base64.b64decode(GOOGLE_CREDENTIALS_B64).decode('utf-8')
    print(">>> PRIMEROS 50 CARACTERES:", creds_json_str[:50])
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as tmp:
        tmp.write(creds_json_str)
        tmp_path = tmp.name
    
    creds = ServiceAccountCredentials.from_json_keyfile_name(tmp_path, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    print(">>> CONEXION A GOOGLE SHEETS OK")
except Exception as e:
    print(">>> ERROR CRITICO GOOGLE SHEETS:", e)

def crear_usuario(email, password, nombre, celular, rol):
    if not sheet: return False
    cupos = 50 if rol == "inmobiliaria" else 3
    usuarios_ws = sheet.worksheet("Usuarios")
    usuarios_ws.append_row([email, password, rol, nombre, celular, cupos, 0, "pendiente"])
    return True

def get_user(email):
    if not sheet: return None
    users = sheet.worksheet("Usuarios").get_all_records()
    for u in users:
        if u['email'] == email and u['estado'] == 'activo':
            return u
    return None

@app.route("/")
def login():
    return "<h2>Login DatoArriendo</h2><form method=post action=/login>Email:<input name=email><br>Password:<input name=password type=password><br><button>Entrar</button></form><a href=/registro>Registro</a>"

@app.route("/registro", methods=["GET","POST"])
def registro():
    if request.method=="GET":
        return "<h2>Registro</h2><form method=post>Nombre:<input name=nombre><br>Celular:<input name=celular><br>Email:<input name=email><br>Password:<input name=password><br>Rol:<select name=rol><option value=arrendador>Arrendador</option><option value=inmobiliaria>Inmobiliaria</option></select><br><button>Crear</button></form>"
    crear_usuario(request.form['email'], request.form['password'], request.form['nombre'], request.form['celular'], request.form['rol'])
    return "Cuenta creada. <a href='/'>Login</a>"

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user['password']) == request.form['password']:
        session['user'] = user
        return "Bienvenido! <a href='/logout'>Salir</a>"
    return "Login invalido"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
