from flask import Flask, request, session, redirect, render_template_string, send_from_directory
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, datetime, uuid

app = Flask(__name__)
app.secret_key = "datoarriendo_2026_segura"

SHEET_ID = os.environ.get("SHEET_ID")
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

CSS = """ <style> body {font-family: Arial; background: #f4f6f8; margin: 0; padding: 0;}.page-wrapper {min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 20px;}.container {background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 400px; max-width: 90%; text-align: center; margin-bottom: 30px;}.dashboard {background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 90%; max-width: 1000px; text-align: left; margin: 20px;}.logo {width: 120px; margin-bottom: 15px;} h2 {color: #2c3e50; margin-bottom: 20px; text-align: center;} h3 {color: #3498db; border-bottom: 2px solid #EBF5FB; padding-bottom: 10px;} input, select, textarea {width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box;} label {font-size: 12px; color: #555; text-align: left; display: block; margin-bottom: 3px; font-weight: bold;} button {width: 100%; padding: 12px; background: #3498db; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; margin-top: 10px;} button:hover {background: #2980b9;} button:disabled {background: #95a5a6; cursor: not-allowed;}.btn-small {width: auto; padding: 8px 16px; font-size: 14px;}.btn-success {background: #27ae60;}.btn-success:hover {background: #229954;}.btn-reportar {background: #e67e22;}.btn-reportar:hover {background: #d35400;}.btn-link {background: #3498db; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; text-decoration: none;}.btn-link:hover {background: #2980b9;}.btn-danger {background: #e74c3c; color: white; padding: 5px 10px; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;}.btn-danger:hover {background: #c0392b;} a {color: #3498db; text-decoration: none; display: block; margin-top: 15px; font-size: 14px;} a:hover {text-decoration: underline;}.info-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;}.info-item {background: #f8f9fa; padding: 12px; border-radius: 8px;}.info-item b {color: #2c3e50;} table {width: 100%; border-collapse: collapse; margin-top: 15px;} th, td {padding: 10px; border-bottom: 1px solid #eee; font-size: 13px; text-align: left;} th {background: #EBF5FB; color: #2c3e50;}.form-inline {display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px;}.badge {padding: 4px 8px; border-radius: 4px; font-size: 12px; color: white;}.badge-activo {background: #27ae60;} @media (max-width: 900px) {.info-grid,.form-inline {grid-template-columns: 1fr;}} </style> """

def crear_usuario(email, password, nombre, celular, rol):
    if not sheet: return False
    cupos_totales = 50 if rol == "inmobiliaria" else 3
    plan = "Plan Inmobiliaria" if rol == "inmobiliaria" else "Plan Básico"
    sheet.worksheet("Usuarios").append_row([email, password, rol, nombre, celular, cupos_totales, 0, "activo", "", plan])
    return True

def get_user(email):
    try:
        users = sheet.worksheet("Usuarios").get_all_records()
        for u in users:
            if str(u.get('email','')).strip().lower() == email.strip().lower() and str(u.get('estado','')) == 'activo':
                return u
    except Exception as e:
        print("Error get_user:", e)
    return None

def get_arrendatarios(email_usuario):
    try:
        ws = sheet.worksheet("Arrendatarios")
        todos = ws.get_all_values()
        if len(todos) < 2: return []
        headers = [h.strip() for h in todos[0]]
        data = []
        for row in todos[1:]:
            if len(row) < len(headers): row += [''] * (len(headers) - len(row))
            registro = dict(zip(headers, row))
            if str(registro.get('email_propietario','')).strip().lower() == email_usuario.strip().lower():
                data.append(registro)
        return data
    except Exception as e:
        print("Error get_arrendatarios:", e)
        return []

def get_reportados_base(email_usuario):
    try:
        ws = sheet.worksheet("Base_Universal")
        todos = ws.get_all_values()
        if len(todos) < 2: return []
        headers = [h.strip() for h in todos[0]]
        data = []
        for row in todos[1:]:
            if len(row) < len(headers): row += [''] * (len(headers) - len(row))
            registro = dict(zip(headers, row))
            if str(registro.get('email_propietario','')).strip().lower() == email_usuario.strip().lower():
                data.append(registro)
        return data
    except Exception as e:
        print("Error get_reportados_base:", e)
        return []

def add_solo_arrendatario(data):
    try:
        # 1. GUARDAR EN ARRENDATARIOS - 10 COLUMNAS
        fila_arr = [
            data['email_propietario'], data.get('nombre',''), data.get('cedula',''), data.get('celular',''), data.get('correo',''),
            data.get('fecha_inicio',''), data.get('fecha_fin',''), data.get('meses_totales','0'), data.get('pagos_totales','0'),
            data.get('evidencias','')
        ]
        sheet.worksheet("Arrendatarios").append_row(fila_arr)

        # 2. TAMBIEN GUARDAR EN BASE_UNIVERSAL COMO "BUEN PAGADOR"
        meses = int(data.get('meses_totales','0') or 0)
        fila_base = [
            data['email_propietario'], data.get('nombre',''), data.get('cedula',''), data.get('celular',''), data.get('correo',''),
            data.get('fecha_inicio',''), data.get('fecha_fin',''), data.get('meses_totales','0'), data.get('pagos_totales','0'),
            str(meses), "0", "SI", data.get('evidencias','') # pagos_tiempo=meses, dias_atraso=0, paz_salvo=SI
        ]
        sheet.worksheet("Base_Universal").append_row(fila_base)
        return True
    except Exception as e:
        print(">>> ERROR AL GUARDAR ARRENDATARIO:", e)
        return False

def reportar_a_base(data):
    try:
        # SOLO GUARDA EN BASE_UNIVERSAL COMO "MAL PAGADOR"
        fila_base = [
            data['email_propietario'], data.get('nombre',''), data.get('cedula',''), data.get('celular',''), data.get('correo',''),
            data.get('fecha_inicio',''), data.get('fecha_fin',''), data.get('meses_totales','0'), data.get('pagos_totales','0'),
            data.get('pagos_tiempo','0'), data.get('dias_atraso','0'), data.get('paz_salvo',''), data.get('evidencias','')
        ]
        sheet.worksheet("Base_Universal").append_row(fila_base)
        return True
    except Exception as e:
        print(">>> ERROR AL REPORTAR:", e)
        return False

def delete_arrendatario(email_usuario, cedula):
    try:
        ws = sheet.worksheet("Arrendatarios")
        todos = ws.get_all_values()
        for idx, row in enumerate(todos[1:]):
            if len(row) >= 3 and str(row[0]).strip().lower() == email_usuario.strip().lower() and str(row[2]).strip() == cedula.strip():
                ws.delete_rows(idx + 2)
                return True
    except Exception as e: 
        print("Error eliminando:", e)
    return False

@app.route("/")
def login():
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><img src="/logo.jpeg" class="logo"><h2>DatoArriendo</h2><p>Historial Crediticio de Arriendo</p><form method="post" action="/login"><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><button>Entrar</button></form><a href="/registro">¿No tienes cuenta? Regístrate aquí</a></div></div>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><img src="/logo.jpeg" class="logo"><h2>Registro</h2><form method="post"><input name="nombre" placeholder="Nombre Completo / Razón Social" required><input name="celular" placeholder="Celular" required><input name="email" type="email" placeholder="Email" required><input name="password" type="password" placeholder="Password" required><select name="rol" required><option value="">Seleccione tipo...</option><option value="arrendador">Arrendador - 3 arriendos</option><option value="inmobiliaria">Inmobiliaria - 50 arriendos</option></select><button>Crear Cuenta</button></form><a href="/">← Volver al Login</a></div></div>""")
    crear_usuario(request.form['email'], request.form['password'], request.form['nombre'], request.form['celular'], request.form['rol'])
    return render_template_string(CSS + """<div class="page-wrapper"><div class="container"><h2>Cuenta Creada!</h2><p>Ya puedes iniciar sesión</p><a href='/'>Ir a Login</a></div></div>""")

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
    reportados = get_reportados_base(user['email'])
    
    num_arriendos = len(arrendatarios)
    limite = 50 if user['rol'] == "inmobiliaria" else 3
    arriendos_disponibles = limite - num_arriendos

    mensaje_consulta = ""
    if request.method == "POST":
        if 'btn_consultar' in request.form:
            cedula_buscar = request.form['cedula_consulta']
            try:
                base = sheet.worksheet("Base_Universal").get_all_records()
                historiales = [p for p in base if str(p.get('cedula','')).strip() == cedula_buscar]
                if historiales:
                    total_meses = sum(int(h.get('meses_totales',0)) for h in historiales)
                    total_tiempo = sum(int(h.get('pagos_tiempo',0)) for h in historiales)
                    mensaje_consulta = f"<div style='padding:12px; background:#27ae60; color:white; border-radius:8px; margin:10px 0;'><b>Historial encontrado:</b> {historiales[0].get('nombre')}<br>{total_tiempo} de {total_meses} meses pagados a tiempo. Último atraso máx: {historiales[-1].get('dias_atraso')} días</div>"
                else: mensaje_consulta = "<div style='padding:12px; background:#7f8c8d; color:white; border-radius:8px; margin:10px 0;'>Cédula sin historial en Base Universal</div>"
            except: mensaje_consulta = "<div style='padding:12px; background:#e74c3c; color:white; border-radius:8px; margin:10px 0;'>Error: Revisa Base_Universal</div>"

        elif 'btn_agregar' in request.form:
            if arriendos_disponibles > 0:
                data = request.form.to_dict(); data['email_propietario'] = user['email']
                if add_solo_arrendatario(data):
                    return redirect("/dashboard?msg=agregado")
            else:
                return redirect("/dashboard?msg=sin_cupos")

        elif 'btn_reportar_form' in request.form:
            if arriendos_disponibles > 0:
                data = request.form.to_dict(); data['email_propietario'] = user['email']
                if reportar_a_base(data):
                    return redirect("/dashboard?msg=reportado")

        elif 'btn_eliminar' in request.form:
            if delete_arrendatario(user['email'], request.form['cedula_eliminar']):
                return redirect("/dashboard")

    plan = user.get('plan', 'N/A') or 'N/A'

    filas_agregados = ""
    for i in arrendatarios:
        link_contrato = i.get('evidencias_contrato','')
        btn_link = f"<a href='{link_contrato}' target='_blank' class='btn-link'>Ver Docs</a>" if link_contrato else "-"
        fila_html = f"""<tr><td>{i.get('nombre','')}</td><td>{i.get('cedula','')}</td><td>{i.get('celular','')}</td><td>{i.get('fecha_inicio','')}</td><td>{i.get('fecha_fin','')}</td><td>{i.get('meses_totales','0')}</td><td>{btn_link}</td><td><form method="post" style="display:inline;"><input type="hidden" name="cedula_eliminar" value="{i.get('cedula','')}"><button name="btn_eliminar" class="btn-danger">X</button></form></td></tr>"""
        filas_agregados += fila_html

    filas_reportados = ""
    for i in reportados:
        link_contrato = i.get('evidencias_contrato','')
        btn_link = f"<a href='{link_contrato}' target='_blank' class='btn-link'>Ver Docs</a>" if link_contrato else "-"
        fila_html = f"""<tr><td>{i.get('nombre','')}</td><td>{i.get('cedula','')}</td><td>{i.get('pagos_tiempo','0')}/{i.get('meses_totales','0')} meses</td><td>{i.get('dias_atraso','0')} días</td><td>{i.get('paz_salvo','')}</td><td>{btn_link}</td></tr>"""
        filas_reportados += fila_html

    alerta = ""
    if request.args.get('msg') == 'agregado': alerta = "<div style='padding:10px; background:#3498db; color:white; border-radius:8px; margin-bottom:15px;'>Arrendatario agregado correctamente y registrado como buen pagador.</div>"
    if request.args.get('msg') == 'reportado': alerta = "<div style='padding:10px; background:#2ecc71; color:white; border-radius:8px; margin-bottom:15px;'>Arrendatario reportado en Base Universal.</div>"
    if request.args.get('msg') == 'sin_cupos': alerta = f"<div style='padding:10px; background:#e74c3c; color:white; border-radius:8px; margin-bottom:15px;'>Ya llegaste al límite de {limite} arriendos</div>"

    info_grid = f"""<h3>1. Información de tu Cuenta</h3><div class="info-grid"><div class="info-item"><b>Nombre:</b> {user.get('nombre','')}</div><div class="info-item"><b>Correo:</b> {user.get('email','')}</div><div class="info-item"><b>Celular:</b> {user.get('celular','')}</div><div class="info-item"><b>Rol:</b> {user.get('rol','').capitalize()}</div><div class="info-item"><b>Plan:</b> {plan}</div><div class="info-item"><b>Número de Arriendos:</b> {num_arriendos}</div><div class="info-item"><b>Arriendos Disponibles:</b> {arriendos_disponibles}</div></div>"""

    return render_template_string(CSS + f"""<div style="padding: 20px 0;"><div class="dashboard"><img src="/logo.jpeg" class="logo" style="margin: 0 auto 15px; display: block;"><h2>Perfil de {user.get('nombre','')}</h2>{alerta}{info_grid}<h3>3. Consulta Historial Arrendatario</h3><form method="post" style="display:flex; gap:10px; align-items:center; margin-bottom:20px;"><input name="cedula_consulta" placeholder="Digita cédula a consultar" required style="flex:1;"><button name="btn_consultar" style="width:auto; background:#2c3e50;">Consultar</button></form>{mensaje_consulta}<h3>1.5 Agregar Arrendatario</h3><p style="font-size:12px; color:#6B7280;">Se registra como buen pagador en Base Universal</p><form method="post" class="form-inline"><input name="nombre" placeholder="Nombre Arrendatario" required><input name="cedula" placeholder="Cédula" required><input name="celular" placeholder="Celular"><input name="correo" type="email" placeholder="Correo"><div><label>Fecha Inicio Contrato</label><input name="fecha_inicio" type="date"></div><div><label>Fecha Fin Contrato</label><input name="fecha_fin" type="date"></div><input name="meses_totales" type="number" placeholder="Meses Totales"><input name="pagos_totales" type="number" placeholder="Pagos Totales"><input name="evidencias" placeholder="Link Contrato/Documentos"><button name="btn_agregar" class="btn-small btn-success" {'disabled' if arriendos_disponibles <= 0 else ''}>Agregar</button></form><h3>2. Reportar Historial por No Pago</h3><p style="font-size:12px; color:#6B7280;">Se publica en Base Universal para que otros lo consulten</p><form method="post" class="form-inline"><input name="nombre" placeholder="Nombre Arrendatario" required><input name="cedula" placeholder="Cédula" required><input name="celular" placeholder="Celular"><input name="correo" type="email" placeholder="Correo"><div><label>Fecha Inicio</label><input name="fecha_inicio" type="date"></div><div><label>Fecha Fin</label><input name="fecha_fin" type="date"></div><input name="meses_totales" type="number" placeholder="Meses Totales"><input name="pagos_totales" type="number" placeholder="Pagos Totales"><input name="pagos_tiempo" type="number" placeholder="Meses Pagados a Tiempo"><input name="dias_atraso" type="number" placeholder="Días Máx Atraso"><select name="paz_salvo"><option value="">¿Paz y Salvo?</option><option value="SI">SI</option><option value="NO">NO</option></select><input name="evidencias" placeholder="Link de evidencias"><button name="btn_reportar_form" class="btn-small btn-reportar" {'disabled' if arriendos_disponibles <= 0 else ''}>Reportar a Base</button></form><h3>2.1 Mis Arrendatarios</h3><table><thead><tr><th>Nombre</th><th>Cédula</th><th>Celular</th><th>Fecha Inicio</th><th>Fecha Fin</th><th>Meses Totales</th><th>Contrato</th><th>Acción</th></tr></thead><tbody>{filas_agregados if filas_agregados else '<tr><td colspan=8>No hay arrendatarios agregados</td></tr>'}</tbody></table><h3>2.2 Inquilinos Reportados en Base</h3><table><thead><tr><th>Nombre</th><th>Cédula</th><th>Historial</th><th>Máx Atraso</th><th>Paz y Salvo</th><th>Evidencias</th></tr></thead><tbody>{filas_reportados if filas_reportados else '<tr><td colspan=6>No has reportado inquilinos aún</td></tr>'}</tbody></table><a href='/logout'>Salir</a></div></div>""")

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

if __name__ == "__main__": app.run(host="0.0.0.0", port=10000)
