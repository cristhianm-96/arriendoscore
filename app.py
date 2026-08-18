from flask import Flask, request, session, redirect, render_template_string, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, smtplib, random, datetime, uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "datoarriendo_2026_segura"

SHEET_ID = os.environ.get("SHEET_ID")
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASS = os.environ.get("EMAIL_PASS")
EMAIL_FROM = os.environ.get("EMAIL_FROM")
APP_URL = os.environ.get("APP_URL", "https://tu-app.onrender.com") # Agrega esta variable en Render

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

CSS = """ <style> body {font-family: Arial; background: #f4f6f8; margin: 0; padding: 0;} .page-wrapper {min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;} .container {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 400px; max-width: 90%; text-align: center; margin-bottom: 30px;} .dashboard {background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 90%; max-width: 1000px; text-align: left; margin: 20px;} .logo {width: 120px; margin-bottom: 15px;} h2 {color: #2c3e50; margin-bottom: 20px; text-align: center;} h3 {color: #3498db; border-bottom: 2px solid #EBF5FB; padding-bottom: 10px;} input, select {width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;} button {width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 10px;} button:hover {background: #2980b9;} button:disabled {background: #95a5a6; cursor: not-allowed;} .btn-small {width: auto; padding: 8px 16px; font-size: 14px;} .btn-danger {background: #e74c3c; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;} .btn-danger:hover {background: #c0392b;} a {color: #3498db; text-decoration: none; display: block; margin-top: 15px; font-size: 14px;} a:hover {text-decoration: underline;} .info-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;} .info-item {background: #f8f9fa; padding: 12px; border-radius: 8px;} .info-item b {color: #2c3e50;} table {width: 100%; border-collapse: collapse; margin-top: 15px;} th, td {padding: 10px; border-bottom: 1px solid #eee; font-size: 13px; text-align: left;} th {background: #EBF5FB; color: #2c3e50;} .form-inline {display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 20px;} .codigo {font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #3498db;} .trust-section {display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; width: 100%; max-width: 1000px; padding: 0 20px;} .trust-card {background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 20px; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.06);} .trust-icon {width: 40px; height: 40px; background: #EBF5FB; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin: 0 auto 12px;} .trust-icon svg {width: 22px; height: 22px;} .trust-card h4 {font-size: 14px; font-weight: 600; color: #2c3e50; margin: 0 0 6px 0;} .trust-card p {font-size: 12px; color: #6B7280; line-height: 1.4; margin: 0;} .footer-links {display: flex; justify-content: center; gap: 20px; flex-wrap: wrap; margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee;} .footer-links a {font-size: 12px; color: #6B7280; margin: 0; display: inline;} .footer-links a:hover {color: #3498db;} @media (max-width: 900px) {.trust-section, .info-grid, .form-inline {grid-template-columns: 1fr;}} .badge {padding: 3px 8px; border-radius: 12px; font-size: 11px; color: white;} .badge-pendiente {background: #f39c12;} .badge-activo {background: #27ae60;} </style> """

def enviar_codigo(destinatario, codigo, nombre):
    if not EMAIL_USER or not EMAIL_PASS: return
    cuerpo = f"<h2>Hola {nombre}</h2><p>Tu código de validación para DatoArriendo es:</p><p class='codigo'>{codigo}</p>"
    msg = MIMEMultipart(); msg['From'] = EMAIL_FROM; msg['To'] = destinatario; msg['Subject'] = "Código de validación - DatoArriendo"
    msg.attach(MIMEText(cuerpo, 'html'))
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT); server.starttls(); server.login(EMAIL_USER, EMAIL_PASS); server.sendmail(EMAIL_FROM, destinatario, msg.as_string()); server.quit()
    except Exception as e: print("Error correo:", e)

def enviar_correo_validacion_inquilino(destinatario, nombre, token):
    link = f"{APP_URL}/validar_inquilino?token={token}"
    asunto = "Confirma tu registro en DatoArriendo"
    cuerpo = f"""
    <h2>Hola {nombre}</h2>
    <p>Tu arrendador te ha registrado en <b>DatoArriendo</b>.</p>
    <p>Por la Ley de Habeas Data, necesitamos tu autorización para aparecer en la base.</p>
    <p>Haz click aquí para autorizar: <a href='{link}'>{link}</a></p>
    <p>Si no fuiste tú, ignora este correo.</p>
    """
    msg = MIMEMultipart(); msg['From'] = EMAIL_FROM; msg['To'] = destinatario; msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'html'))
    try:
        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT); server.starttls(); server.login(EMAIL_USER, EMAIL_PASS); server.sendmail(EMAIL_FROM, destinatario, msg.as_string()); server.quit()
        print(f"[OK] Correo validacion enviado a {destinatario}")
        return True
    except Exception as e: print("Error correo inquilino:", e); return False

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
        if str(u.get('email','')).strip() == email and str(u.get('estado','')) == 'activo': 
            u['cupos_totales'] = int(u.get('cupos_totales', 0) or 0)
            u['cupos_usados'] = int(u.get('cupos_usados', 0) or 0)
            return u
    return None

def get_inquilinos(email_usuario):
    try:
        todos = sheet.worksheet("Inquilinos").get_all_records()
        # SOLO MUESTRA LOS ACTIVOS
        return [i for i in todos if str(i.get('email_propietario','')).strip() == email_usuario and str(i.get('estado','')) == 'activo']
    except: return []

def add_inquilino(data):
    token = str(uuid.uuid4()) # Token único para validación
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
    # ESTADO PENDIENTE AL INICIO
    sheet.worksheet("Inquilinos").append_row([
        data['email_propietario'], data['nombre'], data['cedula'], data['celular'], 
        data['correo'], data['fecha_pago'], data['reporte'], data['info_adicional'], fecha, "pendiente", token
    ])
    
    # Enviar correo solo si puso correo
    if data['correo']:
        enviar_correo_validacion_inquilino(data['correo'], data['nombre'], token)

def activar_inquilino(token):
    ws = sheet.worksheet("Inquilinos")
    inquilinos = ws.get_all_records()
    for idx, i in enumerate(inquilinos):
        if str(i.get('token','')) == token and str(i.get('estado','')) == 'pendiente':
            fila = idx + 2
            ws.update_cell(fila, 10, "activo") # Columna 10 = estado
            ws.update_cell(fila, 11, "") # Borra token
            
            # Ahora sí resta el cupo
            email_prop = i.get('email_propietario')
            ws_user = sheet.worksheet("Usuarios"); cell = ws_user.find(email_prop)
            cupos_usados = int(ws_user.cell(cell.row, 7).value or 0)
            ws_user.update_cell(cell.row, 7, cupos_usados + 1)
            return True
    return False

def delete_inquilino(email_usuario, cedula):
    try:
        ws = sheet.worksheet("Inquilinos")
        inquilinos = ws.get_all_records()
        for idx, r in enumerate(inquilinos):
            if str(r.get('email_propietario','')) == email_usuario and str(r.get('cedula','')) == cedula:
                ws.delete_rows(idx + 2)
                return True
    except Exception as e: print("Error eliminando:", e)
    return False

@app.route("/")
def login():
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><img src="/logo.jpeg" class="logo"><h2>DatoArriendo</h2><form method="post" action="/login"><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><button>Entrar</button></form><a href="/registro">¿No tienes cuenta? Regístrate aquí</a><div class="footer-links"><a href="/politica-privacidad" target="_blank">Política de Privacidad</a><a href="/terminos" target="_blank">Términos y Condiciones</a><a href="/faq" target="_blank">Preguntas Frecuentes</a><a href="/soporte" target="_blank">Servicio al Cliente</a></div></div></div>""")

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

# NUEVA RUTA PARA VALIDAR INQUILINO
@app.route("/validar_inquilino")
def validar_inquilino():
    token = request.args.get('token')
    if activar_inquilino(token):
        return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>✅ Autorización Exitosa</h2><p>Has autorizado aparecer en DatoArriendo. Tu arrendador ya puede gestionarte.</p></div></div>""")
    else:
        return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>❌ Link Inválido</h2><p>Este link ya fue usado o no existe.</p></div></div>""")

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user.get('password','')) == request.form['password']: session['user'] = user; return redirect("/dashboard")
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Error</h2><p>Login inválido</p><a href='/'>Volver</a></div></div>""")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    user = session.get('user');
    if not user: return redirect("/")
    user['cupos_totales'] = int(user.get('cupos_totales', 0) or 0)
    user['cupos_usados'] = int(user.get('cupos_usados', 0) or 0)
    mensaje_consulta = ""
    if request.method == "POST":
        if 'btn_consultar' in request.form:
            cedula_buscar = request.form['cedula_consulta']
            try:
                base = sheet.worksheet("Base_Universal").get_all_records()
                encontrado = None
                for persona in base:
                    if str(persona.get('cedula','')).strip() == cedula_buscar: encontrado = persona; break
                if encontrado:
                    estado = encontrado.get('estado','').strip().lower()
                    color = "#e74c3c" if estado == "moroso" else "#27ae60"
                    mensaje_consulta = f"<div style='padding:12px; background:{color}; color:white; border-radius:8px; margin:10px 0;'><b>Resultado:</b> {encontrado.get('nombre')} está <b>{encontrado.get('estado')}</b></div>"
                else: mensaje_consulta = "<div style='padding:12px; background:#7f8c8d; color:white; border-radius:8px; margin:10px 0;'>Cédula sin reportes en Base Universal</div>"
            except: mensaje_consulta = "<div style='padding:12px; background:#e74c3c; color:white; border-radius:8px; margin:10px 0;'>Error: Crea la pestaña Base_Universal</div>"
        elif 'btn_agregar' in request.form:
            data = request.form.to_dict(); data['email_propietario'] = user['email']
            cupos_disp = user['cupos_totales'] - user['cupos_usados']
            if cupos_disp > 0:
                add_inquilino(data)
                return redirect("/dashboard?msg=correo_enviado")
        elif 'btn_eliminar' in request.form:
            cedula_eliminar = request.form['cedula_eliminar']
            if delete_inquilino(user['email'], cedula_eliminar):
                return redirect("/dashboard")
    inquilinos = get_inquilinos(user['email'])
    cupos_disp = user['cupos_totales'] - user['cupos_usados']
    plan = user.get('plan', 'N/A') or 'N/A'
    filas = ""
    for i inquilinos:
        filas += f"""<tr><td>{i.get('nombre','')}</td><td>{i.get('cedula','')}</td><td>{i.get('celular','')}</td><td>{i.get('correo','')}</td><td>{i.get('fecha_pago','')}</td><td>{i.get('reporte','')}</td><td>{i.get('info_adicional','')}</td><td><form method="post" style="margin:0;"><input type="hidden" name="cedula_eliminar" value="{i.get('cedula','')}"><button name="btn_eliminar" class="btn-danger" onclick="return confirm('¿Eliminar?')">X</button></form></td></tr>"""
    
    alerta = "<div style='padding:10px; background:#2ecc71; color:white; border-radius:8px; margin-bottom:15px;'>Correo de validación enviado al inquilino. Aparecerá cuando autorice.</div>" if request.args.get('msg') == 'correo_enviado' else ""
    
    return render_template_string(CSS + f"""<div style="padding: 20px 0;"><div class="dashboard"><img src="/logo.jpeg" class="logo" style="margin: 0 auto 15px; display: block;"><h2>Perfil de {user.get('nombre','')}</h2>{alerta}<h3>1. Información de tu Cuenta</h3><div class="info-grid"><div class="info-item"><b>Nombre:</b> {user.get('nombre','')}</div><div class="info-item"><b>Correo:</b> {user.get('email','')}</div><div class="info-item"><b>Celular:</b> {user.get('celular','')}</div><div class="info-item"><b>Rol:</b> {user.get('rol','').capitalize()}</div><div class="info-item"><b>Plan:</b> {plan}</div><div class="info-item"><b>Consultas Disponibles:</b> {cupos_disp}</div><div class="info-item"><b>Número de Inquilinos:</b> {len(inquilinos)}</div></div><h3>3. Consulta Base Universal</h3><form method="post" style="display:flex; gap:10px; align-items:center; margin-bottom:20px;"><input name="cedula_consulta" placeholder="Digita cédula a validar" required style="flex:1;"><button name="btn_consultar" style="width:auto; background:#2c3e50;">Consultar</button></form>{mensaje_consulta}<h3>2. Gestión de Inquilinos</h3><form method="post" class="form-inline"><input name="nombre" placeholder="Nombre Inquilino" required><input name="cedula" placeholder="Cédula" required><input name="celular" placeholder="Celular"><input name="correo" type="email" placeholder="Correo Obligatorio" required><input name="fecha_pago" type="date"><input name="reporte" placeholder="Reporte: Al día / Moroso"><input name="info_adicional" placeholder="Info Adicional" style="grid-column: span 3;"><button name="btn_agregar" class="btn-small" {'disabled' if cupos_disp <= 0 else ''}>Agregar</button></form><table><thead><tr><th>Nombre</th><th>Cédula</th><th>Celular</th><th>Correo</th><th>Fecha Pago</th><th>Reporte</th><th>Info</th><th>Acción</th></tr></thead><tbody>{filas if filas else '<tr><td colspan=8>No hay inquilinos activos</td></tr>'}</tbody></table><a href='/logout'>Salir</a></div></div>""")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__": app.run(host="0.0.0.0", port=10000)
