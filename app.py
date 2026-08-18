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

CSS = """ <style> body {font-family: Arial; background: #f4f6f8; margin: 0; padding: 0;}.page-wrapper {min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;}.container {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 400px; max-width: 90%; text-align: center; margin-bottom: 30px;}.dashboard {background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 90%; max-width: 1000px; text-align: left; margin: 20px;}.logo {width: 120px; margin-bottom: 15px;} h2 {color: #2c3e50; margin-bottom: 20px; text-align: center;} h3 {color: #3498db; border-bottom: 2px solid #EBF5FB; padding-bottom: 10px;} input, select, textarea {width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;} label {font-size: 12px; color: #555; text-align: left; display: block; margin-bottom: 3px; font-weight: bold;} button {width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 10px;} button:hover {background: #2980b9;} button:disabled {background: #95a5a6; cursor: not-allowed;}.btn-small {width: auto; padding: 8px 16px; font-size: 14px;}.btn-success {background: #27ae60;}.btn-success:hover {background: #229954;}.btn-reportar {background: #e67e22;}.btn-reportar:hover {background: #d35400;}.btn-danger {background: #e74c3c; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;}.btn-danger:hover {background: #c0392b;} a {color: #3498db; text-decoration: none; display: block; margin-top: 15px; font-size: 14px;} a:hover {text-decoration: underline;}.info-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;}.info-item {background: #f8f9fa; padding: 12px; border-radius: 8px;}.info-item b {color: #2c3e50;} table {width: 100%; border-collapse: collapse; margin-top: 15px;} th, td {padding: 10px; border-bottom: 1px solid #eee; font-size: 13px; text-align: left;} th {background: #EBF5FB; color: #2c3e50;}.form-inline {display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px;}.codigo {font-size: 32px; letter-spacing: 8px; font-weight: bold; color: #3498db;}.badge {padding: 4px 8px; border-radius: 4px; font-size: 12px; color: white;}.badge-agregado {background: #3498db;}.badge-activo {background: #27ae60;}.badge-pendiente {background: #f39c12;}.badge-disputa {background: #e74c3c;} @media (max-width: 900px) {.info-grid,.form-inline {grid-template-columns: 1fr;}} </style> """

def enviar_codigo(destinatario, codigo, nombre):
    def _enviar():
        if not EMAIL_USER or not EMAIL_PASS: return
        cuerpo = f"<h2>Hola {nombre}</h2><p>Tu código de validación para DatoArriendo es:</p><p class='codigo'>{codigo}</p>"
        msg = MIMEMultipart(); msg['From'] = EMAIL_FROM; msg['To'] = destinatario; msg['Subject'] = "Código de validación - DatoArriendo"
        msg.attach(MIMEText(cuerpo, 'html'))
        try:
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
            server.starttls(); server.login(EMAIL_USER, EMAIL_PASS); server.sendmail(EMAIL_FROM, destinatario, msg.as_string()); server.quit()
        except Exception as e: print("Error correo:", e)
    threading.Thread(target=_enviar, daemon=True).start()

def enviar_correo_validacion_arrendatario(destinatario, nombre, token, datos_reporte):
    def _enviar():
        try:
            link_aceptar = f"{APP_URL}/validar_arrendatario?token={token}&accion=aceptar"
            link_disputa = f"{APP_URL}/validar_arrendatario?token={token}&accion=disputar"
            asunto = "Tienes un reporte en DatoArriendo - 7 días para responder"
            cuerpo = f"""<html><body style="font-family:Arial;"><h2>Hola {nombre}</h2><p>Tu arrendador te ha registrado en <b>DatoArriendo</b></p><p><b>Periodo:</b> {datos_reporte.get('fecha_inicio')} a {datos_reporte.get('fecha_fin')}<br><b>Pagos a tiempo:</b> {datos_reporte.get('pagos_tiempo')} de {datos_reporte.get('meses_totales')} meses</p><p><a href='{link_aceptar}' style='padding:12px; background:#27ae60; color:white; text-decoration:none;'>Aceptar</a> <a href='{link_disputa}' style='padding:12px; background:#e74c3c; color:white; text-decoration:none;'>Disputar</a></p></body></html>"""
            msg = MIMEMultipart(); msg['From'] = EMAIL_FROM; msg['To'] = destinatario; msg['Subject'] = asunto
            msg.attach(MIMEText(cuerpo, 'html'))
            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=10)
            server.starttls(); server.login(EMAIL_USER, EMAIL_PASS); server.sendmail(EMAIL_FROM, destinatario, msg.as_string()); server.quit()
        except Exception as e: print("Error correo arrendatario:", e)
    threading.Thread(target=_enviar, daemon=True).start()

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
            return u
    return None

def get_arrendatarios(email_usuario):
    try:
        todos = sheet.worksheet("Arrendatarios").get_all_records()
        return [i for i in todos if str(i.get('email_propietario','')).strip() == email_usuario]
    except: return []

def add_arrendatario(data):
    token = str(uuid.uuid4())
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
    fecha_limite = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    fila_completa = [data['email_propietario'], data['nombre'], data['cedula'], data['celular'], data['correo'], data['fecha_inicio'], data['fecha_fin'], data['meses_totales'], data['pagos_totales'], data['pagos_tiempo'], data['dias_atraso'], data['paz_salvo'], data['evidencias'], fecha, fecha_limite, "agregado", token, ""]
    sheet.worksheet("Arrendatarios").append_row(fila_completa)
    sheet.worksheet("Base_Universal").append_row(fila_completa)

def reportar_arrendatario(email_propietario, cedula):
    ws = sheet.worksheet("Arrendatarios")
    arrendatarios = ws.get_all_records()
    for idx, i in enumerate(arrendatarios):
        if str(i.get('email_propietario','')) == email_propietario and str(i.get('cedula','')) == cedula:
            fila = idx + 2
            ws.update_cell(fila, 16, "activo") # Cambia estado
            token = i.get('token')
            if i.get('correo'):
                enviar_correo_validacion_arrendatario(i.get('correo'), i.get('nombre'), token, i)
            # Actualizar tambien en Base_Universal
            ws_base = sheet.worksheet("Base_Universal")
            base = ws_base.get_all_records()
            for idx2, b in enumerate(base):
                if str(b.get('email_propietario','')) == email_propietario and str(b.get('cedula','')) == cedula:
                    ws_base.update_cell(idx2 + 2, 16, "activo")
            return True
    return False

def activar_arrendatario(token, accion, comentario=""):
    ws = sheet.worksheet("Arrendatarios")
    arrendatarios = ws.get_all_records()
    for idx, i in enumerate(arrendatarios):
        if str(i.get('token','')) == token:
            fila = idx + 2
            if accion == "aceptar": ws.update_cell(fila, 16, "activo")
            else: ws.update_cell(fila, 16, "en_disputa"); ws.update_cell(fila, 18, comentario)
            ws.update_cell(fila, 17, "")
            return True
    return False

def delete_arrendatario(email_usuario, cedula):
    try:
        ws = sheet.worksheet("Arrendatarios")
        arrendatarios = ws.get_all_records()
        for idx, r in enumerate(arrendatarios):
            if str(r.get('email_propietario','')) == email_usuario and str(r.get('cedula','')) == cedula:
                ws.delete_rows(idx + 2)
                return True
    except Exception as e: print("Error eliminando:", e)
    return False

@app.route("/")
def login():
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><img src="/logo.jpeg" class="logo"><h2>DatoArriendo</h2><p>Historial Crediticio de Arriendo</p><form method="post" action="/login"><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><button>Entrar</button></form><a href="/registro">¿No tienes cuenta? Regístrate aquí</a></div></div>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><img src="/logo.jpeg" class="logo"><h2>Registro</h2><form method="post"><input name="nombre" placeholder="Nombre Completo / Razón Social" required><input name="celular" placeholder="Celular" required><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><select name="rol" required><option value="">Seleccione tipo...</option><option value="arrendador">Arrendador - 3 arriendos</option><option value="inmobiliaria">Inmobiliaria - 50 arriendos</option></select><button>Crear Cuenta</button></form><a href="/">← Volver al Login</a></div></div>""")
    codigo = str(random.randint(100000, 999))
    crear_usuario_temp(request.form['email'], request.form['password'], request.form['nombre'], request.form['celular'], request.form['rol'], codigo)
    enviar_codigo(request.form['email'], codigo, request.form['nombre']); session['email_temp'] = request.form['email']; return redirect("/validar")

@app.route("/validar", methods=["GET", "POST"])
def validar():
    email = session.get('email_temp');
    if request.method == "POST":
        if activar_usuario(email, request.form['codigo']): session.pop('email_temp'); return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Cuenta Activada!</h2><a href='/'>Ir a Login</a></div></div>""")
        else: return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Código incorrecto</h2></div></div>""")
    return render_template_string(CSS + f"""<div class="page-wrapper"><div class="container"><h2>Valida tu correo</h2><p>Código enviado a: <b>{email}</b></p><form method="post"><input name="codigo" placeholder="Código de 6 dígitos" required><button>Validar</button></form></div></div>""")

@app.route("/validar_arrendatario")
def validar_arrendatario():
    token = request.args.get('token')
    accion = request.args.get('accion')
    comentario = request.args.get('comentario', '')
    if activar_arrendatario(token, accion, comentario):
        return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Respuesta registrada</h2><p>Tu respuesta fue enviada.</p></div></div>""")
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>❌ Link Inválido</h2></div></div>""")

@app.route("/login", methods=["POST"])
def login_post():
    user = get_user(request.form['email'])
    if user and str(user.get('password','')) == request.form['password']: session['user'] = user; return redirect("/dashboard")
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Error</h2><p>Login inválido</p><a href='/'>Volver</a></div></div>""")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    user = session.get('user');
    if not user: return redirect("/")

    arrendatarios = get_arrendatarios(user['email'])
    num_arriendos = len(arrendatarios)
    limite = 50 if user['rol'] == "inmobiliaria" else 3
    arriendos_disponibles = limite - num_arriendos

    mensaje_consulta = ""
    if request.method == "POST":
        if 'btn_consultar' in request.form:
            cedula_buscar = request.form['cedula_consulta']
            try:
                base = sheet.worksheet("Base_Universal").get_all_records()
                historiales = [p for p in base if str(p.get('cedula','')).strip() == cedula_buscar and str(p.get('estado','')) == 'activo']
                if historiales:
                    total_meses = sum(int(h.get('meses_totales',0)) for h in historiales)
                    total_tiempo = sum(int(h.get('pagos_tiempo',0)) for h in historiales)
                    mensaje_consulta = f"<div style='padding:12px; background:#27ae60; color:white; border-radius:8px; margin:10px 0;'><b>Historial encontrado:</b> {historiales[0].get('nombre')}<br>{total_tiempo} de {total_meses} meses pagados a tiempo. Último atraso máx: {historiales[-1].get('dias_atraso')} días</div>"
                else: mensaje_consulta = "<div style='padding:12px; background:#7f8c8d; color:white; border-radius:8px; margin:10px 0;'>Cédula sin historial en Base Universal</div>"
            except: mensaje_consulta = "<div style='padding:12px; background:#e74c3c; color:white; border-radius:8px; margin:10px 0;'>Error: Crea la pestaña Base_Universal</div>"

        elif 'btn_agregar' in request.form:
            if arriendos_disponibles > 0:
                data = request.form.to_dict(); data['email_propietario'] = user['email']
                add_arrendatario(data)
                return redirect("/dashboard?msg=agregado")
            else:
                return redirect("/dashboard?msg=sin_cupos")

        elif 'btn_reportar' in request.form:
            if reportar_arrendatario(user['email'], request.form['cedula_reportar']):
                return redirect("/dashboard?msg=reportado")
            else:
                return redirect("/dashboard?msg=error")

        elif 'btn_eliminar' in request.form:
            if delete_arrendatario(user['email'], request.form['cedula_eliminar']):
                return redirect("/dashboard")

    plan = user.get('plan', 'N/A') or 'N/A'

    filas_agregados = ""
    filas_reportados = ""
    for i in arrendatarios:
        estado = i.get('estado','')
        badge_class = "badge-agregado" if estado == "agregado" else "badge-activo" if estado == "activo" else "badge-pendiente" if "pendiente" in estado else "badge-disputa"

        fila_html = f"""<tr><td>{i.get('nombre','')}</td><td>{i.get('cedula','')}</td><td>{i.get('pagos_tiempo','')}/{i.get('meses_totales','')} meses</td><td>{i.get('dias_atraso','')} días</td><td><span class="badge {badge_class}">{estado}</span></td><td>"""

        if estado == "agregado":
            fila_html += f"""<form method="post" style="display:inline; margin-right:5px;"><input type="hidden" name="cedula_reportar" value="{i.get('cedula','')}"><button name="btn_reportar" class="btn-reportar" style="padding:5px 10px; font-size:12px;">Reportar</button></form>"""

        fila_html += f"""<form method="post" style="display:inline;"><input type="hidden" name="cedula_eliminar" value="{i.get('cedula','')}"><button name="btn_eliminar" class="btn-danger">X</button></form></td></tr>"""

        if estado == "agregado":
            filas_agregados += fila_html
        else:
            filas_reportados += fila_html

    alerta = ""
    if request.args.get('msg') == 'agregado': alerta = "<div style='padding:10px; background:#3498db; color:white; border-radius:8px; margin-bottom:15px;'>Arrendatario agregado a tu perfil y Base Universal.</div>"
    if request.args.get('msg') == 'reportado': alerta = "<div style='padding:10px; background:#2ecc71; color:white; border-radius:8px; margin-bottom:15px;'>Arrendatario reportado. Se envió correo para validación.</div>"
    if request.args.get('msg') == 'sin_cupos': alerta = f"<div style='padding:10px; background:#e74c3c; color:white; border-radius:8px; margin-bottom:15px;'>Ya llegaste al límite de {limite} arriendos de tu plan</div>"

    info_grid = f"""<h3>1. Información de tu Cuenta</h3><div class="info-grid"><div class="info-item"><b>Nombre:</b> {user.get('nombre','')}</div><div class="info-item"><b>Correo:</b> {user.get('email','')}</div><div class="info-item"><b>Celular:</b> {user.get('celular','')}</div><div class="info-item"><b>Rol:</b> {user.get('rol','').capitalize()}</div><div class="info-item"><b>Plan:</b> {plan}</div><div class="info-item"><b>Número de Arriendos:</b> {num_arriendos}</div><div class="info-item"><b>Arriendos Disponibles:</b> {arriendos_disponibles}</div></div>"""

    return render_template_string(CSS + f"""<div style="padding: 20px 0;"><div class="dashboard"><img src="/logo.jpeg" class="logo" style="margin: 0 auto 15px; display: block;"><h2>Perfil de {user.get('nombre','')}</h2>{alerta}{info_grid}<h3>3. Consulta Historial Arrendatario</h3><form method="post" style="display:flex; gap:10px; align-items:center; margin-bottom:20px;"><input name="cedula_consulta" placeholder="Digita cédula a consultar" required style="flex:1;"><button name="btn_consultar" style="width:auto; background:#2c3e50;">Consultar</button></form>{mensaje_consulta}<h3>1.5 Agregar Arrendatario</h3><p style="font-size:12px; color:#6B7280;">Se guarda en tu perfil y en Base Universal con estado 'agregado'. Para activar el reporte usa el botón 'Reportar'.</p><form method="post" class="form-inline"><input name="nombre" placeholder="Nombre Arrendatario" required><input name="cedula" placeholder="Cédula" required><input name="celular" placeholder="Celular"><input name="correo" type="email" placeholder="Correo"><div><label>Fecha Inicio Contrato</label><input name="fecha_inicio" type="date"></div><div><label>Fecha Fin Contrato</label><input name="fecha_fin" type="date"></div><input name="meses_totales" type="number" placeholder="Meses Totales"><input name="pagos_totales" type="number" placeholder="Valor Total Pagado"><input name="pagos_tiempo" type="number" placeholder="Meses Pagados a Tiempo"><input name="dias_atraso" type="number" placeholder="Días Máx Atraso"><select name="paz_salvo"><option value="">¿Paz y Salvo?</option><option value="SI">SI</option><option value="NO">NO</option></select><input name="evidencias" placeholder="Link a Drive con evidencias"><button name="btn_agregar" class="btn-small btn-success" {'disabled' if arriendos_disponibles <= 0 else ''}>Agregar</button></form><h3>2. Mis Arrendatarios Agregados</h3><table><thead><tr><th>Nombre</th><th>Cédula</th><th>Historial</th><th>Máx Atraso</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{filas_agregados if filas_agregados else '<tr><td colspan=6>No hay arrendatarios agregados</td></tr>'}</tbody></table><h3>2.1 Mis Arrendatarios Reportados</h3><table><thead><tr><th>Nombre</th><th>Cédula</th><th>Historial</th><th>Máx Atraso</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{filas_reportados if filas_reportados else '<tr><td colspan=6>No hay arrendatarios reportados</td></tr>'}</tbody></table><a href='/logout'>Salir</a></div></div>""")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__": app.run(host="0.0.0.0", port=10000)
