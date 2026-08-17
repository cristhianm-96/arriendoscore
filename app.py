from flask import Flask, request, session, redirect, render_template_string
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cambia_esta_clave_por_una_segura_datoarriendo_123"
print(">>> DATOARRIENDO INICIANDO...")

# 1. Leer variables de Render
SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDENTIALS_JSON = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON", "{}").replace('\\n', '\n'))
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")

# 2. Conectar con Google Sheets
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
sheet = None
try:
    print(">>> INTENTANDO CONECTAR A GOOGLE...")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    print(">>> CONEXION A GOOGLE SHEETS OK")
except Exception as e:
    print(">>> ERROR CRITICO GOOGLE SHEETS:", e)

def enviar_correo(destinatario, nombre, rol):
    if not GMAIL_USER or not GMAIL_PASSWORD:
        print("Faltan variables GMAIL_USER o GMAIL_PASSWORD")
        return False
    
    cupos = 50 if rol == "inmobiliaria" else 3
    asunto = "Bienvenido a DatoArriendo"
    cuerpo = f"""
    <html><body style="font-family:Arial;">
        <h2 style="color:#2c3e50;">Hola {nombre}</h2>
        <p>Tu cuenta en <b>DatoArriendo</b> ha sido creada exitosamente.</p>
        <p><b>Tipo de cuenta:</b> {rol.capitalize()}<br>
        <b>Cupos asignados:</b> {cupos}</p>
        <p style="background:#f8f9fa; padding:15px;">Tu cuenta está en estado 'pendiente'. La activaremos pronto.</p>
        <p>Saludos,<br><b>Equipo DatoArriendo</b></p>
    </body></html>
    """
    msg = MIMEMultipart()
    msg['From'] = GMAIL_USER
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'html'))
    
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, destinatario, msg.as_string())
        server.quit()
        print(f"Correo enviado a {destinatario}")
        return True
    except Exception as e:
        print("Error enviando correo:", e)
        return False

def get_user(email):
    if not sheet: return None
    try:
        users = sheet.worksheet("Usuarios").get_all_records()
        for u in users:
            if u['email'] == email and u['estado'] == 'activo':
                return u
    except Exception as e: print("Error get_user:", e)
    return None

def crear_usuario(email, password, nombre, celular, rol):
    print(f">>> CREANDO USUARIO: {email}")
    if not sheet: return False
    cupos = 50 if rol == "inmobiliaria" else 3
    usuarios_ws = sheet.worksheet("Usuarios")
    usuarios_ws.append_row([email, password, rol, nombre, celular, cupos, 0, "pendiente"])
    enviar_correo(email, nombre, rol)
    print(">>> USUARIO GUARDADO EN SHEET")
    return True

def buscar_cedula(cc):
    if not sheet: return None
    try:
        autorizaciones = sheet.worksheet("Autorizaciones").get_all_records()
        for a in autorizaciones:
            if str(a['cc']) == str(cc):
                return a
    except Exception as e: print("Error buscar_cedula:", e)
    return None

def reportar(cc, motivo, user):
    if not sheet: return "Error: No hay conexión con Sheet"
    cupos_disp = int(user['cupos_totales']) - int(user['cupos_usados'])
    if cupos_disp <= 0:
        return "Error: No tienes cupos disponibles"
    
    reportes = sheet.worksheet("Reportes")
    reportes.append_row([cc, motivo, user['email'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    
    usuarios_ws = sheet.worksheet("Usuarios")
    cell = usuarios_ws.find(user['email'])
    nuevo_cupo = int(user['cupos_usados']) + 1
    usuarios_ws.update_cell(cell.row, 7, nuevo_cupo)
    
    return f"Reporte guardado. Cupos restantes: {cupos_disp - 1}"

# 4. Rutas HTML con branding DatoArriendo
@app.route("/")
def login():
    return render_template_string("""<html><head><title>DatoArriendo Login</title></head>
    <body style="font-family:Arial; max-width:400px; margin:50px auto;">
        <h2 style="color:#2c3e50;">Login DatoArriendo</h2>
        <form method="post" action="/login">
            Email: <br><input name="email" type="email" required style="width:100%; padding:8px;"><br><br>
            Password: <br><input name="password" type="password" required style="width:100%; padding:8px;"><br><br>
            <button style="padding:10px 20px; background:#3498db; color:white; border:none; cursor:pointer;">Entrar</button>
        </form>
        <br><p>¿No tienes cuenta? <a href="/registro">Regístrate aquí</a></p>
    </body></html>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string("""<html><head><title>Registro DatoArriendo</title></head>
        <body style="font-family:Arial; max-width:400px; margin:50px auto;">
            <h2 style="color:#2c3e50;">Registro DatoArriendo</h2>
            <form method="post">
                Nombre/Razón Social: <br><input name="nombre" required style="width:100%; padding:8px;"><br><br>
                Celular: <br><input name="celular" required style="width:100%; padding:8px;"><br><br>
                Email: <br><input name="email" type="email" required style="width:100%; padding:8px;"><br><br>
                Password: <br><input name="password" type="password" required style="width:100%; padding:8px;"><br><br>
                Tipo de cuenta: <br>
                <select name="rol" required style="width:100%; padding:8px;">
                    <option value="">Seleccione...</option>
                    <option value="arrendador">Arrendador - Hasta 3 consultas</option>
                    <option value="inmobiliaria">Inmobiliaria - Hasta 50 consultas</option>
                </select><br><br>
                <button style="padding:10px 20px; background:#27ae60; color:white; border:none;">Crear Cuenta</button>
            </form>
            <br><a href="/">Volver a Login</a>
        </body></html>""")
    
    email = request.form['email']
    if not sheet: return "Error: No hay conexión con Google Sheets. Revisa Logs"
    usuarios_ws = sheet.worksheet("Usuarios").get_all_records()
    if any(u['email'] == email for u in usuarios_ws):
        return "Ese email ya existe. <a href='/registro'>Intentar otra vez</a>"
    
    crear_usuario(request.form['email'], request.form['password'], request.form['nombre'], request.form['celular'], request.form['rol'])
    return "Cuenta creada en DatoArriendo. Queda en estado 'pendiente'. <a href='/'>Ir a Login</a>"

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form['email']
    password = request.form['password']
    user = get_user(email)
    if user and str(user['password']) == password:
        session['user'] = user
        return redirect("/dashboard")
    return "Login invalido o cuenta pendiente de activación. <a href='/'>Volver</a>"

@app.route("/dashboard")
def dashboard():
    user = session.get('user')
    if not user: return redirect("/")
    cupos_disp = int(user['cupos_totales']) - int(user['cupos_usados'])
    tipo = "Inmobiliaria - 50 consultas" if user['rol'] == "inmobiliaria" else "Arrendador - 3 consultas"
    return render_template_string(f"""<html><head><title>DatoArriendo Dashboard</title></head>
    <body style="font-family:Arial; max-width:600px; margin:30px auto;">
        <h2>Bienvenido a DatoArriendo, {user['nombre']}</h2>
        <p><b>Rol:</b> {tipo} | <b>Consultas disponibles:</b> {cupos_disp}</p><hr>
        <h3>Consultar Autorización</h3>
        <form method="post" action="/buscar">
            Buscar por cédula: <input name="cc" required>
            <button>Buscar</button>
        </form>
        <br><a href='/logout'>Salir</a>
    </body></html>""")

@app.route("/buscar", methods=["POST"])
def buscar():
    user = session.get('user')
    if not user: return redirect("/")
    cc = request.form['cc']
    resultado = buscar_cedula(cc)
    if resultado:
        return render_template_string(f"""<html><body style="font-family:Arial; max-width:600px; margin:30px auto;">
        <h3>Resultado DatoArriendo</h3>
        <b>CC:</b> {resultado['cc']}<br><b>Celular:</b> {resultado['celular']}<br>
        <b>Estado:</b> <span style="color:green;">{resultado['estado']}</span><br>
        <b>Fecha Autorización:</b> {resultado['fecha_autorizacion']}<br><b>Código:</b> {resultado['codigo']}<br><br>
        <h4>Reportar</h4>
        <form method="post" action="/reportar">
            <input type="hidden" name="cc" value="{cc}">
            Motivo: <input name="motivo" placeholder="Ej: Mora 2 meses" required>
            <button>Reportar y descontar consulta</button>
        </form>
        <br><a href='/dashboard'>Buscar otra cédula</a>
        </body></html>""")
    return f"No se encontró CC {cc} en DatoArriendo <br><a href='/dashboard'>Volver</a>"

@app.route("/reportar", methods=["POST"])
def reportar_post():
    user = session.get('user')
    if not user: return redirect("/")
    msg = reportar(request.form['cc'], request.form['motivo'], user)
    return f"<p>{msg}</p><a href='/dashboard'>Volver</a>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
