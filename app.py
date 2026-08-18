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

CSS = """ ... tu mismo CSS ... """

def enviar_codigo(destinatario, codigo, nombre):
    if not GMAIL_USER or not GMAIL_PASSWORD: return
    cuerpo = f"<h2>Hola {nombre}</h2><p>Tu código de validación para DatoArriendo es:</p><p class='codigo'>{codigo}</p>"
    msg = MIMEMultipart(); msg['From'] = GMAIL_USER; msg['To'] = destinatario; msg['Subject'] = "Código de validación - DatoArriendo"
    msg.attach(MIMEText(cuerpo, 'html'))
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465); server.login(GMAIL_USER, GMAIL_PASSWORD); server.sendmail(GMAIL_USER, destinatario, msg.as_string()); server.quit()
    except Exception as e: print("Error correo:", e)

def crear_usuario_temp(email, password, nombre, celular, rol, codigo):
    if not sheet: return False
    cupos = 50 if rol == "inmobiliaria" else 3
    plan = "Plan Inmobiliaria" if rol == "inmobiliaria" else "Plan Básico"
    sheet.worksheet("Usuarios").append_row([email, password, rol, nombre, celular, cupos, 0, "pendiente", codigo, plan])
    return True

def activar_usuario(email, codigo):
    ws = sheet.worksheet("Usuarios"); cell = ws.find(email)
    if cell and str(ws.cell(cell.row, 9).value) == codigo:
        ws.update_cell(cell.row, 8, "activo"); ws.update_cell(cell.row, 9, ""); return True
    return False

def get_user(email):
    users = sheet.worksheet("Usuarios").get_all_records()
    for u in users:
        if str(u.get('email','')).strip() == email and str(u.get('estado','')) == 'activo': return u
    return None

def get_inquilinos(email_usuario):
    try:
        todos = sheet.worksheet("Inquilinos").get_all_records()
        return [i for i in todos if str(i.get('email_propietario','')) == email_usuario]
    except: return []

def add_inquilino(data):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
    sheet.worksheet("Inquilinos").append_row([data['email_propietario'], data['nombre'], data['cedula'], data['celular'], data['correo'], data['fecha_pago'], data['reporte'], data['info_adicional'], fecha])
    sheet.worksheet("Autorizaciones").append_row([data['email_propietario'], data['cedula'], data['nombre'], "Autoriza registro", fecha])
    sheet.worksheet("Reportes").append_row([data['cedula'], data['nombre'], data['reporte'], data['email_propietario'], fecha, data['info_adicional']])

@app.route("/")
def login():
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><img src="/logo.jpeg" class="logo"><h2>DatoArriendo</h2><form method="post" action="/login"><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><button>Entrar</button></form><a href="/registro">¿No tienes cuenta? Regístrate aquí</a></div><div class="trust-section"><div class="trust-card"><div class="trust-icon"><svg viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg></div><h4>Información 100% Segura</h4><p>Cumplimos con la Ley 1581 de Habeas Data.</p></div><div class="trust-card"><div class="trust-icon"><svg viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><h4>Evita Arrendatarios Morosos</h4><p>Consulta reportes antes de firmar.</p></div><div class="trust-card"><div class="trust-icon"><svg viewBox="0 0 24 24" fill="none" stroke="#3498db" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg></div><h4>Usado por Inmobiliarias</h4><p>Verificación rápida y confiable.</p></div></div></div>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><img src="/logo.jpeg" class="logo"><h2>Registro</h2><form method="post"><input name="nombre" placeholder="Nombre Completo / Razón Social" required><input name="celular" placeholder="Celular" required><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><select name="rol" required><option value="">Seleccione tipo...</option><option value="arrendador">Arrendador - 3 consultas</option><option value="inmobiliaria">Inmobiliaria - 50 consultas</option></select><button>Crear Cuenta</button></form><a href="/">← Volver al Login</a></div></div>""")
    codigo = str(random.randint(100000, 999))
    crear_usuario_temp(request.form['email'], request.form['password'], request.form['nombre'], request.form['celular'], request.form['rol'], codigo)
    enviar_codigo(request.form['email'], codigo, request.form['nombre']); session['email_temp'] = request.form['email']; return redirect("/validar")

@app.route("/validar", methods=["GET", "POST"])
def validar():
    email = session.get('email_temp');
    if request.method == "POST":
        if activar_usuario(email, request.form['codigo']): session.pop('email_temp'); return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Cuenta Activada!</h2><a href='/'>Ir a Login</a></div></div>""")
        else: return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Código incorrecto</h2><a href='/validar'>Intentar</a></div></div>""")
    return render_template_string(CSS + f"""<div class="page-wrapper"><div class="container"><h2>Valida tu correo</h2><p>Código enviado a: <b>{email}</b></p><form method="post"><input name="codigo" placeholder="Código de 6 dígitos" required><button>Validar</button></form></div></div>""")

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user.get('password','')) == request.form['password']: session['user'] = user; return redirect("/dashboard")
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Error</h2><p>Login inválido</p><a href='/'>Volver</a></div></div>""")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    user = session.get('user');
    if not user: return redirect("/")
    
    mensaje_consulta = ""
    if request.method == "POST":
        if 'btn_consultar' in request.form:
            cedula_buscar = request.form['cedula_consulta']
            try:
                base = sheet.worksheet("Base_Universal").get_all_records()
                encontrado = None
                for persona in base:
                    if str(persona.get('cedula','')).strip() == cedula_buscar:
                        encontrado = persona
                        break
                if encontrado:
                    color = "#c0392b" if encontrado.get('estado') == "Moroso" else "#27ae60"
                    mensaje_consulta = f"<div style='padding:12px; background:{color}; color:white; border-radius:8px; margin:10px 0;'><b>Resultado:</b> {encontrado.get('nombre')} está <b>{encontrado.get('estado')}</b></div>"
                else:
                    mensaje_consulta = "<div style='padding:12px; background:#7f8c8d; color:white; border-radius:8px; margin:10px 0;'>Cédula sin reportes en Base Universal</div>"
            except Exception as e:
                mensaje_consulta = "<div style='padding:12px; background:#e74c3c; color:white; border-radius:8px; margin:10px 0;'>Error: Crea la pestaña Base_Universal con columnas: cedula, nombre, estado</div>"

        elif 'btn_agregar' in request.form:
            data = request.form.to_dict(); data['email_propietario'] = user['email']
            cupos_totales = int(user.get('cupos_totales', 0) or 0)
            cupos_usados = int(user.get('cupos_usados', 0) or 0)
            if cupos_totales - cupos_usados > 0:
                add_inquilino(data)
                ws = sheet.worksheet("Usuarios"); cell = ws.find(user['email'])
                ws.update_cell(cell.row, 7, cupos_usados + 1)
                user['cupos_usados'] = cupos_usados + 1; session['user'] = user; return redirect("/dashboard")
    
    inquilinos = get_inquilinos(user['email'])
    cupos_disp = int(user.get('cupos_totales',0) or 0) - int(user.get('cupos_usados',0) or 0)
    plan = user.get('plan', 'N/A') or 'N/A'
    
    filas = ""
    for i inquilinos:
        filas += f"<tr><td>{i.get('nombre','')}</td><td>{i.get('cedula','')}</td><td>{i.get('celular','')}</td><td>{i.get('correo','')}</td><td>{i.get('fecha_pago','')}</td><td>{i.get('reporte','')}</td><td>{i.get('info_adicional','')}</td></tr>"
    
    return render_template_string(CSS + f"""<div style="padding: 20px 0;"><div class="dashboard"><img src="/logo.jpeg" class="logo" style="margin: 0 auto 15px; display: block;"><h2>Perfil de {user.get('nombre','')}</h2><h3>1. Información de tu Cuenta</h3><div class="info-grid"><div class="info-item"><b>Nombre:</b> {user.get('nombre','')}</div><div class="info-item"><b>Correo:</b> {user.get('email','')}</div><div class="info-item"><b>Celular:</b> {user.get('celular','')}</div><div class="info-item"><b>Rol:</b> {user.get('rol','').capitalize()}</div><div class="info-item"><b>Plan:</b> {plan}</div><div class="info-item"><b>Consultas Disponibles:</b> {cupos_disp}</div><div class="info-item"><b>Número de Arriendos:</b> {len(inquilinos)}</div></div>
    
    <h3>3. Consulta Base Universal</h3>
    <form method="post" style="display:flex; gap:10px; align-items:center; margin-bottom:20px;">
        <input name="cedula_consulta" placeholder="Digita cédula a validar" required style="flex:1;">
        <button name="btn_consultar" style="width:auto; background:#2c3e50;">Consultar</button>
    </form>
    {mensaje_consulta}
    
    <h3>2. Gestión de Inquilinos</h3><form method="post" class="form-inline"><input name="nombre" placeholder="Nombre Inquilino" required><input name="cedula" placeholder="Cédula" required><input name="celular" placeholder="Celular"><input name="correo" type="email" placeholder="Correo"><input name="fecha_pago" type="date"><input name="reporte" placeholder="Reporte: Al día / Moroso"><input name="info_adicional" placeholder="Info Adicional" style="grid-column: span 3;"><button name="btn_agregar" class="btn-small" {'disabled' if cupos_disp <= 0 else ''}>Agregar</button></form><table><thead><tr><th>Nombre</th><th>Cédula</th><th>Celular</th><th>Correo</th><th>Fecha Pago</th><th>Reporte</th><th>Info</th></tr></thead><tbody>{filas if filas else '<tr><td colspan=7>No hay inquilinos</td></tr>'}</tbody></table><a href='/logout'>Salir</a></div></div>""")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__": app.run(host="0.0.0.0", port=10000)
