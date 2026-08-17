from flask import Flask, request, session, redirect, render_template_string, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "datoarriendo_2026_segura"
print(">>> DATOARRIENDO INICIANDO...")

SHEET_ID = os.environ.get("SHEET_ID")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
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

# Para servir el logo
@app.route('/logo.jpeg')
def serve_logo():
    return send_from_directory('.', 'logo.jpeg')

CSS = """
<style>
body {font-family: Arial; background: #f4f6f8; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;}
.container {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 400px; text-align: center;}
.logo {width: 120px; margin-bottom: 15px;}
h2 {color: #2c3e50; margin-bottom: 20px;}
input, select {width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;}
button {width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer;}
button:hover {background: #2980b9;}
a {color: #3498db; text-decoration: none;}
</style>
"""

def enviar_correo(destinatario, nombre, rol):
    if not GMAIL_USER or not GMAIL_PASSWORD: return
    cupos = 50 if rol == "inmobiliaria" else 3
    cuerpo = f"<h2>Hola {nombre}</h2><p>Tu cuenta {rol} en DatoArriendo fue creada. Cupos: {cupos}</p>"
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = "Bienvenido a DatoArriendo"
    msg.attach(MIMEText(cuerpo, 'html'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, destinatario, msg.as_string())
        server.quit()
    except Exception as e:
        print("Error correo:", e)

def crear_usuario(email, password, nombre, celular, rol):
    if not sheet: return False
    cupos = 50 if rol == "inmobiliaria" else 3
    usuarios_ws = sheet.worksheet("Usuarios")
    usuarios_ws.append_row([email, password, rol, nombre, celular, cupos, 0, "pendiente"])
    enviar_correo(email, nombre, rol)
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
    return render_template_string(CSS + """
    <div class="container">
        <img src="/logo.jpeg" class="logo">
        <h2>DatoArriendo</h2>
        <form method="post" action="/login">
            <input name="email" type="email" placeholder="Email" required>
            <input name="password" type="password" placeholder="Password" required>
            <button>Entrar</button>
        </form>
        <br><a href="/registro">¿No tienes cuenta? Regístrate aquí</a>
    </div>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string(CSS + """
        <div class="container">
            <img src="/logo.jpeg" class="logo">
            <h2>DatoArriendo</h2>
            <form method="post">
                <input name="nombre" placeholder="Nombre Completo" required>
                <input name="celular" placeholder="Celular" required>
                <input name="email" type="email" placeholder="Email" required>
                <input name="password" type="password" placeholder="Password" required>
                <select name="rol" required>
                    <option value="">Seleccione tipo...</option>
                    <option value="arrendador">Arrendador - 3 consultas</option>
                    <option value="inmobiliaria">Inmobiliaria - 50 consultas</option>
                </select>
                <button>Crear Cuenta</button>
            </form>
        </div>""")
    crear_usuario(request.form['email'], request.form['password'], request.form['nombre'], request.form['celular'], request.form['rol'])
    return render_template_string(CSS + """<div class="container"><img src="/logo.jpeg" class="logo"><h2>Cuenta Creada!</h2><p>Estado: pendiente de aprobación</p><a href='/'>Ir a Login</a></div>""")

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user['password']) == request.form['password']:
        session['user'] = user
        return redirect("/dashboard")
    return render_template_string(CSS + """<div class="container"><h2>Error</h2><p>Login inválido</p><a href='/'>Volver</a></div>""")

@app.route("/dashboard")
def dashboard():
    user = session.get('user')
    if not user: return redirect("/")
    cupos_disp = int(user['cupos_totales']) - int(user['cupos_usados'])
    return render_template_string(CSS + f"""
    <div class="container">
        <img src="/logo.jpeg" class="logo">
        <h2>Bienvenido {user['nombre']}</h2>
        <p><b>Consultas disponibles:</b> {cupos_disp}</p>
        <a href='/logout'>Salir</a>
    </div>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
