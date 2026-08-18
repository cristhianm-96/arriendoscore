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
body {font-family: Arial; background: #f4f6f8; margin: 0; padding: 20px 0;}
.page {display: flex; flex-direction: column; justify-content: center; align-items: center; min-height: 100vh;}
.container {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 400px; text-align: center;}
.logo {width: 120px; margin-bottom: 15px;}
h2 {color: #2c3e50; margin-bottom: 20px;}
input, select {width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;}
button {width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 10px;}
button:hover {background: #2980b9;}
.btn-volver {background: #95a5a6;}
.btn-volver:hover {background: #7f8c8d;}
a {color: #3498db; text-decoration: none; display: block; margin-top: 15px;}
.codigo {font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #3498db;}

/* CUADROS DE CONFIANZA */
.trust-section {display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; max-width: 900px; margin: 40px auto 0; padding: 0 20px;}
.trust-card {background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 24px 20px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.05); transition: all 0.2s ease;}
.trust-card:hover {box-shadow: 0 4px 12px rgba(52, 152, 219, 0.15); transform: translateY(-2px);}
.trust-icon {width: 48px; height: 48px; background: #EBF5FB; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px;}
.trust-icon svg {width: 24px; height: 24px;}
.trust-card h4 {font-size: 15px; font-weight: 600; color: #2c3e50; margin: 0 0 8px 0;}
.trust-card p {font-size: 13px; color: #6B7280; line-height: 1.5; margin: 0;}
@media (max-width: 768px) {.trust-section {grid-template-columns: 1fr; gap: 16px;}}
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
    usuarios_ws = sheet.worksheet("Usuarios")
    usuarios_ws.append_row([email, password, rol, nombre, celular, cupos, 0, "pendiente", codigo])
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

        <!-- CUADROS DE CONFIANZA -->
        <div class="trust-section">
            <div class="trust-card">
                <div class="trust-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2">
                        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                    </svg>
                </div>
                <h4>Información 100% Segura</h4>
                <p>Cumplimos con la Ley 1581 de Habeas Data. Tus datos y los de tus arrendatarios están protegidos.</p>
            </div>

            <div class="trust-card">
                <div class="trust-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                        <polyline points="22 4 12 14.01 9 11.01"/>
                    </svg>
                </div>
                <h4>Evita Arrendatarios Morosos</h4>
                <p>Consulta el historial de pagos y reportes antes de firmar. Toma decisiones con datos reales.</p>
            </div>

            <div class="trust-card">
                <div class="trust-icon">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                        <circle cx="9" cy="7" r="4"/>
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                    </svg>
                </div>
                <h4>Usado por Inmobiliarias</h4>
                <p>La herramienta de confianza para verificar arrendatarios en Colombia. Rápido y confiable.</p>
            </div>
        </div>
    </div>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string(CSS + """
        <div class="page">
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
                <a href="/">← Volver al Login</a>
            </div>
        </div>""")
    
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
            return render_template_string(CSS + """<div class="page"><div class="container"><h2>Código incorrecto</h2><p>Revisa tu correo</p><a href='/validar'>Intentar de nuevo</a><a href='/'>← Volver al Login</a></div></div>""")
    
    return render_template_string(CSS + f"""
    <div class="page">
        <div class="container">
            <img src="/logo.jpeg" class="logo">
            <h2>Valida tu correo</h2>
            <p>Te enviamos un código de 6 dígitos a: <b>{email}</b></p>
            <form method="post">
                <input name="codigo" placeholder="Código de 6 dígitos" required maxlength="6">
                <button>Validar Cuenta</button>
            </form>
            <a href="/">← Volver al Login</a>
        </div>
    </div>""")

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user['password']) == request.form['password']:
        session['user'] = user
        return redirect("/dashboard")
    return render_template_string(CSS + """<div class="page"><div class="container"><h2>Error</h2><p>Login inválido o cuenta pendiente</p><a href='/'>Volver</a></div></div>""")

@app.route("/dashboard")
def dashboard():
    user = session.get('user')
    if not user: return redirect("/")
    cupos_disp = int(user['cupos_totales']) - int(user['cupos_usados'])
    return render_template_string(CSS + f"""
    <div class="page">
        <div class="container">
            <img src="/logo.jpeg" class="logo">
            <h2>Bienvenido {user['nombre']}</h2>
            <p><b>Consultas disponibles:</b> {cupos_disp}</p>
            <a href='/logout'>Salir</a>
        </div>
    </div>""")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
