from flask import Flask, request, session, redirect, render_template_string, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, smtplib, random, datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client # NUEVO

app = Flask(__name__)
app.secret_key = "datoarriendo_2026_segura"

SHEET_ID = os.environ.get("SHEET_ID")
GMAIL_USER = os.environ.get("GMAIL_USER")
GMAIL_PASSWORD = os.environ.get("GMAIL_PASSWORD")
CREDS_PATH = "/etc/secrets/credentials.json"

# TWILIO
TWILIO_SID = os.environ.get("TWILIO_SID")
TWILIO_TOKEN = os.environ.get("TWILIO_TOKEN")
TWILIO_PHONE = os.environ.get("TWILIO_PHONE")

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

def enviar_sms(celular, codigo, nombre):
    if not TWILIO_SID or not TWILIO_TOKEN: 
        print("Faltan credenciales Twilio")
        return
    try:
        client_tw = Client(TWILIO_SID, TWILIO_TOKEN)
        mensaje = f"DatoArriendo: {nombre} te reporto como inquilino. Autoriza con codigo: {codigo}. Si no fuiste tu, ignora."
        client_tw.messages.create(body=mensaje, from_=TWILIO_PHONE, to=f"+57{celular}")
        print(f">>> SMS enviado a +57{celular}")
    except Exception as e: print("Error SMS:", e)

def enviar_codigo(destinatario, codigo, nombre): ... igual ...

def crear_usuario_temp(email, password, nombre, celular, rol, codigo): ... igual ...

def activar_usuario(email, codigo): ... igual ...

def get_user(email): ... igual ...

def get_inquilinos(email_usuario):
    try:
        todos = sheet.worksheet("Inquilinos").get_all_records()
        return [i for i in todos if str(i.get('email_propietario','')).strip() == email_usuario]
    except: return []

def add_inquilino_pendiente(data, codigo_auth):
    fecha = datetime.datetime.now().strftime("%Y-%m-%d")
    # Guardar en Inquilinos con estado pendiente
    sheet.worksheet("Inquilinos").append_row([
        data['email_propietario'], data['nombre'], data['cedula'], data['celular'], 
        data['correo'], data['fecha_pago'], data['reporte'], data['info_adicional'], 
        fecha, "pendiente", codigo_auth
    ])
    # Enviar SMS al inquilino
    enviar_sms(data['celular'], codigo_auth, data['nombre'])

def autorizar_inquilino(cedula, codigo):
    ws = sheet.worksheet("Inquilinos")
    inquilinos = ws.get_all_records()
    for idx, i in enumerate(inquilinos):
        if str(i.get('cedula','')) == cedula and str(i.get('codigo_auth','')) == codigo:
            fila = idx + 2
            ws.update_cell(fila, 10, "autorizado") # Columna J
            ws.update_cell(fila, 11, "") # Borrar código Columna K
            
            # Copiar a Base_Universal
            fecha = datetime.datetime.now().strftime("%Y-%m-%d")
            try:
                base_ws = sheet.worksheet("Base_Universal")
                base = base_ws.get_all_records()
                existe = False
                for idx2, persona in enumerate(base):
                    if str(persona.get('cedula','')).strip() == cedula:
                        existe = True
                        fila2 = idx2 + 2
                        base_ws.update_cell(fila2, 2, i['nombre'])
                        base_ws.update_cell(fila2, 3, i['reporte'])
                        base_ws.update_cell(fila2, 4, i['email_propietario'])
                        base_ws.update_cell(fila2, 5, fecha)
                        break
                if not existe:
                    base_ws.append_row([cedula, i['nombre'], i['reporte'], i['email_propietario'], fecha])
            except Exception as e: print("Error Base_Universal:", e)
            return True
    return False

def delete_inquilino(email_usuario, cedula): ... igual ...

@app.route("/")
def login(): ... igual con footer ...

# NUEVA RUTA
@app.route("/autorizar/<cedula>", methods=["GET", "POST"])
def autorizar(cedula):
    if request.method == "POST":
        if autorizar_inquilino(cedula, request.form['codigo']):
            return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Autorizado!</h2><p>Gracias. Ya quedas registrado en la Base Universal</p></div></div>""")
        else:
            return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Código incorrecto</h2><a href='/autorizar/"""+cedula+"""'>Intentar</a></div></div>""")
    return render_template_string(CSS + f"""<div class="page-wrapper"><div class="container"><h2>Autoriza tu registro</h2><p>Te enviamos un código al celular <b>{cedula}</b>. Digítalo aquí:</p><form method="post"><input name="codigo" placeholder="Código de 6 dígitos" required><button>Autorizar</button></form></div></div>""")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    user = session.get('user');
    if not user: return redirect("/")
    user['cupos_totales'] = int(user.get('cupos_totales', 0) or 0)
    user['cupos_usados'] = int(user.get('cupos_usados', 0) or 0)
    mensaje_consulta = ""
    if request.method == "POST":
        if 'btn_consultar' in request.form: ... igual ...
        elif 'btn_agregar' in request.form:
            data = request.form.to_dict(); data['email_propietario'] = user['email']
            cupos_disp = user['cupos_totales'] - user['cupos_usados']
            if cupos_disp > 0:
                codigo_auth = str(random.randint(100000, 999999))
                add_inquilino_pendiente(data, codigo_auth)
                ws = sheet.worksheet("Usuarios"); cell = ws.find(user['email'])
                ws.update_cell(cell.row, 7, user['cupos_usados'] + 1)
                user['cupos_usados'] += 1; session['user'] = user; return redirect("/dashboard")
        elif 'btn_eliminar' in request.form: ... igual ...
    
    inquilinos = get_inquilinos(user['email'])
    cupos_disp = user['cupos_totales'] - user['cupos_usados']
    plan = user.get('plan', 'N/A') or 'N/A'
    filas = ""
    for i in inquilinos:
        estado = i.get('estado_auth','pendiente')
        color = "#f39c12" if estado == "pendiente" else "#27ae60"
        link_auth = f"<a href='/autorizar/{i.get('cedula','')}' target='_blank'>Enviar link</a>" if estado == "pendiente" else "Autorizado"
        filas += f"""<tr style="background:{color}20"><td>{i.get('nombre','')}</td><td>{i.get('cedula','')}</td><td>{i.get('celular','')}</td><td>{i.get('correo','')}</td><td>{i.get('fecha_pago','')}</td><td>{i.get('reporte','')}</td><td><b>{estado.upper()}</b><br>{link_auth}</td><td><form method="post" style="margin:0;"><input type="hidden" name="cedula_eliminar" value="{i.get('cedula','')}"><button name="btn_eliminar" class="btn-danger">X</button></form></td></tr>"""
    
    return render_template_string(CSS + f"""<div style="padding: 20px 0;"><div class="dashboard"><img src="/logo.jpeg" class="logo" style="margin: 0 auto 15px; display: block;"><h2>Perfil de {user.get('nombre','')}</h2><h3>1. Información de tu Cuenta</h3><div class="info-grid"><div class="info-item"><b>Nombre:</b> {user.get('nombre','')}</div><div class="info-item"><b>Correo:</b> {user.get('email','')}</div><div class="info-item"><b>Celular:</b> {user.get('celular','')}</div><div class="info-item"><b>Rol:</b> {user.get('rol','').capitalize()}</div><div class="info-item"><b>Plan:</b> {plan}</div><div class="info-item"><b>Consultas Disponibles:</b> {cupos_disp}</div><div class="info-item"><b>Número de Inquilinos:</b> {len(inquilinos)}</div></div><h3>3. Consulta Base Universal</h3><form method="post" style="display:flex; gap:10px; align-items:center; margin-bottom:20px;"><input name="cedula_consulta" placeholder="Digita cédula a validar" required style="flex:1;"><button name="btn_consultar" style="width:auto; background:#2c3e50;">Consultar</button></form>{mensaje_consulta}<h3>2. Gestión de Inquilinos</h3><form method="post" class="form-inline"><input name="nombre" placeholder="Nombre Inquilino" required><input name="cedula" placeholder="Cédula" required><input name="celular" placeholder="Celular sin +57"><input name="correo" type="email" placeholder="Correo"><input name="fecha_pago" type="date"><input name="reporte" placeholder="Reporte: Al día / Moroso"><input name="info_adicional" placeholder="Info Adicional" style="grid-column: span 3;"><button name="btn_agregar" class="btn-small" {'disabled' if cupos_disp <= 0 else ''}>Agregar</button></form><table><thead><tr><th>Nombre</th><th>Cédula</th><th>Celular</th><th>Correo</th><th>Fecha Pago</th><th>Reporte</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{filas if filas else '<tr><td colspan=8>No hay inquilinos</td></tr>'}</tbody></table><a href='/logout'>Salir</a></div></div>""")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__": app.run(host="0.0.0.0", port=10000)
