from flask import Flask, request, session, redirect, render_template_string
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "cambia_esta_clave_por_una_segura_123"

# 1. Leer variables de Render
SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDENTIALS_JSON = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))

# 2. Conectar con Google Sheets
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

# 3. Funciones
def get_user(email):
    users = sheet.worksheet("Usuarios").get_all_records()
    for u in users:
        if u['email'] == email and u['estado'] == 'activo':
            return u
    return None

def crear_usuario(email, password, nombre, celular, rol):
    """Crea usuario. Inmobiliaria=50 cupos, Arrendador=3 cupos"""
    cupos = 50 if rol == "inmobiliaria" else 3
    usuarios_ws = sheet.worksheet("Usuarios")
    usuarios_ws.append_row([
        email, 
        password, 
        rol,
        nombre,
        celular,
        cupos, # cupos_totales
        0, # cupos_usados
        "pendiente" # estado
    ])
    return True

def buscar_cedula(cc):
    autorizaciones = sheet.worksheet("Autorizaciones").get_all_records()
    for a in autorizaciones:
        if str(a['cc']) == str(cc):
            return a
    return None

def reportar(cc, motivo, user):
    cupos_disp = int(user['cupos_totales']) - int(user['cupos_usados'])
    if cupos_disp <= 0:
        return "Error: No tienes cupos disponibles"
    
    reportes = sheet.worksheet("Reportes")
    reportes.append_row([cc, motivo, user['email'], datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    
    usuarios_ws = sheet.worksheet("Usuarios")
    cell = usuarios_ws.find(user['email'])
    nuevo_cupo = int(user['cupos_usados']) + 1
    usuarios_ws.update_cell(cell.row, 7, nuevo_cupo) # Columna G
    
    return f"Reporte guardado. Cupos restantes: {cupos_disp - 1}"

# 4. Rutas
@app.route("/")
def login():
    return render_template_string("""
    <html>
    <head><title>Arriendoscore Login</title></head>
    <body style="font-family:Arial; max-width:400px; margin:50px auto;">
        <h2>Login Arriendoscore</h2>
        <form method="post" action="/login">
            Email: <br><input name="email" style="width:100%; padding:8px;" required><br><br>
            Password: <br><input name="password" type="password" style="width:100%; padding:8px;" required><br><br>
            <button style="padding:10px 20px;">Entrar</button>
        </form>
        <br>
        <p>¿No tienes cuenta? <a href="/registro">Regístrate aquí</a></p>
    </body></html>""")

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "GET":
        return render_template_string("""
        <html>
        <head><title>Registro</title></head>
        <body style="font-family:Arial; max-width:400px; margin:50px auto;">
            <h2>Registro Arriendoscore</h2>
            <form method="post" action="/registro">
                Nombre: <br><input name="nombre" style="width:100%; padding:8px;" required><br><br>
                Celular: <br><input name="celular" style="width:100%; padding:8px;" required><br><br>
                Email: <br><input name="email" type="email" style="width:100%; padding:8px;" required><br><br>
                Password: <br><input name="password" type="password" style="width:100%; padding:8px;" required><br><br>
                
                Tipo de cuenta: <br>
                <select name="rol" style="width:100%; padding:8px;" required>
                    <option value="">Seleccione...</option>
                    <option value="arrendador">Arrendador - Hasta 3 arriendos</option>
                    <option value="inmobiliaria">Inmobiliaria - Hasta 50 arriendos</option>
                </select><br><br>
                
                <button style="padding:10px 20px;">Crear Cuenta</button>
            </form>
            <br><a href="/">Volver a Login</a>
        </body></html>""")
    
    # POST
    email = request.form['email']
    if get_user(email):
        return "Ese email ya existe. <a href='/registro'>Intentar otra vez</a>"
    
    crear_usuario(
        request.form['email'],
        request.form['password'],
        request.form['nombre'],
        request.form['celular'],
        request.form['rol']
    )
    return "Cuenta creada. Queda en estado 'pendiente'. Un admin debe activarla. <a href='/'>Ir a Login</a>"

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
    tipo = "Inmobiliaria 50" if user['rol'] == "inmobiliaria" else "Arrendador 3"
    return render_template_string(f"""
    <html>
    <head><title>Dashboard</title></head>
    <body style="font-family:Arial; max-width:600px; margin:30px auto;">
        <h2>Bienvenido {user['nombre']}</h2>
        <p><b>Rol:</b> {tipo} | <b>Cupos disponibles:</b> {cupos_disp}</p>
        <hr>
        <h3>Consultar Autorización</h3>
        <form method="post" action="/buscar">
            Buscar por cédula: <input name="cc" required>
            <button>Buscar</button>
        </form>
        <br><a href='/logout'>Salir</a>
    </body></html>
    """)

@app.route("/buscar", methods=["POST"])
def buscar():
    user = session.get('user')
    if not user: return redirect("/")
    cc = request.form['cc']
    resultado = buscar_cedula(cc)
    if resultado:
        return render_template_string(f"""
        <html><body style="font-family:Arial; max-width:600px; margin:30px auto;">
        <h3>Resultado de búsqueda</h3>
        <b>CC:</b> {resultado['cc']}<br>
        <b>Celular:</b> {resultado['celular']}<br>
        <b>Estado:</b> <span style="color:green;">{resultado['estado']}</span><br>
        <b>Fecha Autorización:</b> {resultado['fecha_autorizacion']}<br>
        <b>Código:</b> {resultado['codigo']}<br><br>
        
        <h4>Reportar</h4>
        <form method="post" action="/reportar">
            <input type="hidden" name="cc" value="{cc}">
            Motivo: <input name="motivo" placeholder="Ej: Mora 2 meses" required>
            <button>Reportar y descontar cupo</button>
        </form>
        <br><a href='/dashboard'>Buscar otra cédula</a>
        </body></html>
        """)
    return f"No se encontró CC {cc} <br><a href='/dashboard'>Volver</a>"

@app.route("/reportar", methods=["POST"])
def reportar_post():
    user = session.get('user')
    if not user: return redirect("/")
    cc = request.form['cc']
    motivo = request.form['motivo']
    msg = reportar(cc, motivo, user)
    return f"<p>{msg}</p><a href='/dashboard'>Volver</a>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
