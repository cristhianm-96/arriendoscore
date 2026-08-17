from flask import Flask, request, session, redirect, render_template_string, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, smtplib, random
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "datoarriendo_2026_segura"

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
.codigo {font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #3498db;}
</style>
"""

def enviar_codigo(destinatario, codigo, nombre):
    if not GMAIL_USER or not GMAIL_PASSWORD: return
    cuerpo = f"""
    <h2>Hola {nombre}</h2>
    <p>Tu código de validación para DatoArriendo es:</p>
    <p class='codigo'>{codigo}</p>
    <p>Este código expira en 10 minutos.</p>
    """
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = "Código de validación - DatoArriendo"
    msg.attach(MIMEText(cuerpo, 'html'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, destinatario, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Error correo:", e)
        return False

def crear_usuario_temp(email, password, nombre, celular, rol, codigo):
    if not sheet: return False
    cupos = 50 if rol == "inmobiliaria" else 3
    usuarios_ws = sheet.worksheet("Usuarios")
    # columnas: email,password,rol,nombre,celular,cupos_totales,cupos_usados,estado,codigo
    usuarios_ws.append_row([email, password, rol, nombre, celular, cupos, 0, "pendiente", codigo])
    return True

def activar_usuario(email, codigo):
    if not sheet: return False
    ws = sheet.worksheet("Usuarios")
    users = ws.get_all_records()
    for i, u in enumerate(users, start=2): # start=2 porque fila 1 es header
        if u['email'] == email and str(u['codigo']) == codigo:
            ws.update_cell(i, 8, "activo") # columna 8 = estado
            return True
    return False

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
            <h2>Registro</h2>
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
    
    codigo = str(random.randint(100000, 999999))
    crear_usuario_temp(request.form['email'], request.form['password'], request.form['nombre'], request.form['celular'], request.form['rol'], codigo)
    enviar_codigo(request.form['email'], codigo, request.form['nombre'])
    session['email_temp'] = request.form['email']
    return redirect("/validar")

@app.route("/validar", methods=["GET", "POST"])
def validar():
    email = session.get('email_temp')
    if not email: return redirect("/registro")
    
    if request.method == "POST":
        if activar_usuario(email, request.form['codigo']):
            session.pop('email_temp')
            return render_template_string(CSS + """<div class="container"><img src="/logo.jpeg" class="logo"><h2>Cuenta Activada!</h2><p>Ya puedes iniciar sesión</p><a href='/'>Ir a Login</a></div>""")
        else:
            return render_template_string(CSS + """<div class="container"><h2>Código incorrecto</h2><a href='/validar'>Intentar de nuevo</a></div>""")
    
    return render_template_string(CSS + """
    <div class="container">
        <img src="/logo.jpeg" class="logo">
        <h2>Valida tu correo</h2>
        <p>Te enviamos un código de 6 dígitos a: <b>""" + email + """</b></p>
        <form method="post">
            <input name="codigo" placeholder="Código de 6 dígitos" required maxlength="6">
            <button>Validar Cuenta</button>
        </form>
    </div>""")

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user['password']) == request.form['password']:
        session['user'] = user
        return redirect("/dashboard")
    return render_template_string(CSS + """<div class="container"><h2>Error</h2><p>Login inválido o cuenta pendiente</p><a href='/'>Volver</a></div>""")

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
