from flask import Flask, request, session, redirect, render_template_string, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, smtplib, random, datetime
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
body {font-family: Arial; background: #f4f6f8; margin: 0; padding: 20px 0;}
.page {display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh;}
.container {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 400px; text-align: center;}
.dashboard {background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 90%; max-width: 1000px; text-align: left;}
.logo {width: 120px; margin-bottom: 15px;}
h2 {color: #2c3e50; margin-bottom: 20px; text-align: center;}
h3 {color: #3498db; border-bottom: 2px solid #EBF5FB; padding-bottom: 10px;}
input, select {width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;}
button {width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 10px;}
button:hover {background: #2980b9;}
.btn-small {width: auto; padding: 8px 16px; font-size: 14px;}
a {color: #3498db; text-decoration: none; display: block; margin-top: 15px;}
.info-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;}
.info-item {background: #f8f9fa; padding: 12px; border-radius: 8px;}
.info-item b {color: #2c3e50;}
table {width: 100%; border-collapse: collapse; margin-top: 15px;}
th, td {padding: 10px; border-bottom: 1px solid #eee; font-size: 13px; text-align: left;}
th {background: #EBF5FB; color: #2c3e50;}
.form-inline {display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; margin-bottom: 20px;}
.codigo {font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #3498db;}
@media (max-width: 768px) {.info-grid, .form-inline {grid-template-columns: 1fr;}}
</style>
"""

def enviar_codigo(destinatario, codigo, nombre):
    if not GMAIL_USER or not GMAIL_PASSWORD: return
    cuerpo = f"""<h2>Hola {nombre}</h2><p>Tu código de validación para DatoArriendo es:</p><p class='codigo'>{codigo}</p>"""
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
    except Exception as e:
        print("Error correo:", e)

def crear_usuario_temp(email, password, nombre, celular, rol, codigo):
    if not sheet: return False
    cupos = 50 if rol == "inmobiliaria" else 3
    plan = "Plan Inmobiliaria" if rol == "inmobiliaria" else "Plan Básico"
    usuarios_ws = sheet.worksheet("Usuarios")
    usuarios_ws.append_row([email, password, rol, nombre, celular, cupos, 0, "pendiente", codigo, plan])
    return True

def activar_usuario(email, codigo):
    if not sheet: return False
    ws = sheet.worksheet("Usuarios")
    cell = ws.find(email)
    if cell:
        fila = cell.row
        codigo_guardado = ws.cell(fila, 9).value
        if str(codigo_guardado) == codigo:
            ws.update_cell(fila, 8, "activo")
            ws.update_cell(fila, 9, "")
            return True
    return False

def get_user(email):
    if not sheet: return None
    users = sheet.worksheet("Usuarios").get_all_records()
    for u in users:
        if u['email'] == email and u['estado'] == 'activo':
            return u
    return None

def get_inquilinos(email_usuario):
    if not sheet: return []
    try:
        ws = sheet.worksheet("Inquilinos")
        todos = ws.get_all_records()
        return [i for i in todos if i['email_propietario'] == email_usuario]
    except:
        return []

def add_inquilino(data):
    if not sheet: return False
    ws = sheet.worksheet("Inquilinos")
    ws.append_row([
        data['email_propietario'],
        data['nombre'], data['cedula'], data['celular'], data['correo'],
        data['fecha_pago'], data['reporte'], data['info_adicional'],
        datetime.datetime.now().strftime("%Y-%m-%d")
    ])
    return True

@app.route("/")
def login():
    return render_template_string(CSS + """
    <div class="page">
        <div class="container">
            <img src="/logo.jpeg" class="logo">
            <h2>DatoArriendo</h2>
            <form method="post" action="/login">
                <input name="email" type="email" placeholder="Email" required>
                <input name="password" type="password" placeholder="Password" required>
                <button>Entrar</button>
            </form>
            <a href="/registro">¿No tienes cuenta? Regístrate aquí</a>
        </div>
    </div>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string(CSS + """
        <div class="page"><div class="container">
            <img src="/logo.jpeg" class="logo"><h2>Registro</h2>
            <form method="post">
                <input name="nombre" placeholder="Nombre Completo / Razón Social" required>
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
            <a href="/">← Volver al Login</a>
        </div></div>""")
    
    codigo = str(random.randint(100000, 999))
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
            return render_template_string(CSS + """<div class="page"><div class="container"><img src="/logo.jpeg" class="logo"><h2>Cuenta Activada!</h2><p>Ya puedes iniciar sesión</p><a href='/'>Ir a Login</a></div></div>""")
        else:
            return render_template_string(CSS + """<div class="page"><div class="container"><h2>Código incorrecto</h2><p>Revisa tu correo</p><a href='/validar'>Intentar de nuevo</a></div></div>""")
    return render_template_string(CSS + f"""<div class="page"><div class="container"><img src="/logo.jpeg" class="logo"><h2>Valida tu correo</h2><p>Te enviamos un código a: <b>{email}</b></p><form method="post"><input name="codigo" placeholder="Código de 6 dígitos" required maxlength="6"><button>Validar Cuenta</button></form></div></div>""")

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user['password']) == request.form['password']:
        session['user'] = user
        return redirect("/dashboard")
    return render_template_string(CSS + """<div class="page"><div class="container"><h2>Error</h2><p>Login inválido o cuenta pendiente</p><a href='/'>Volver</a></div></div>""")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    user = session.get('user')
    if not user: return redirect("/")
    
    if request.method == "POST":
        data = request.form.to_dict()
        data['email_propietario'] = user['email']
        add_inquilino(data)
        return redirect("/dashboard")

    inquilinos = get_inquilinos(user['email'])
    cupos_disp = int(user['cupos_totales']) - int(user['cupos_usados'])
    num_arriendos = len(inquilinos)

    filas_tabla = ""
    for i in inquilinos:
        filas_tabla += f"<tr><td>{i['nombre']}</td><td>{i['cedula']}</td><td>{i['celular']}</td><td>{i['correo']}</td><td>{i['fecha_pago']}</td><td>{i['reporte']}</td><td>{i['info_adicional']}</td></tr>"

    return render_template_string(CSS + f"""
    <div class="page">
        <div class="dashboard">
            <img src="/logo.jpeg" class="logo" style="margin: 0 auto 15px; display: block;">
            <h2>Perfil de {user['nombre']}</h2>
            
            <h3>1. Información de tu Cuenta</h3>
            <div class="info-grid">
                <div class="info-item"><b>Nombre/Razón Social:</b> {user['nombre']}</div>
                <div class="info-item"><b>Correo:</b> {user['email']}</div>
                <div class="info-item"><b>Celular:</b> {user['celular']}</div>
                <div class="info-item"><b>Rol:</b> {user['rol'].capitalize()}</div>
                <div class="info-item"><b>Plan:</b> {user['plan']}</div>
                <div class="info-item"><b>Consultas Disponibles:</b> {cupos_disp}</div>
                <div class="info-item"><b>Número de Arriendos Registrados:</b> {num_arriendos}</div>
            </div>

            <h3>2. Gestión de Inquilinos {num_arriendos}/50</h3>
            <form method="post" class="form-inline">
                <input name="nombre" placeholder="Nombre Inquilino" required>
                <input name="cedula" placeholder="Cédula" required>
                <input name="celular" placeholder="Celular">
                <input name="correo" type="email" placeholder="Correo">
                <input name="fecha_pago" type="date" placeholder="Fecha Pago">
                <input name="reporte" placeholder="Reporte: Al día / Moroso">
                <input name="info_adicional" placeholder="Info Adicional" style="grid-column: span 4;">
                <button class="btn-small" {'disabled' if cupos_disp <= 0 else ''}>Agregar</button>
            </form>

            <table>
                <thead><tr>
                    <th>Nombre</th><th>Cédula</th><th>Celular</th><th>Correo</th>
                    <th>Fecha Pago</th><th>Reporte</th><th>Info Adicional</th>
                </tr></thead>
                <tbody>{filas_tabla if filas_tabla else '<tr><td colspan=7 style="text-align:center;">No hay inquilinos registrados</td></tr>'}</tbody>
            </table>

            <a href='/logout' style="text-align:center; margin-top: 30px;">Salir</a>
        </div>
    </div>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
