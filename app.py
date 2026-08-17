from flask import Flask, request, jsonify, session, render_template_string
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = "clave_secreta_cambiala"

SHEET_ID = os.environ.get("SHEET_ID")
GOOGLE_CREDENTIALS_JSON = json.loads(os.environ.get("GOOGLE_CREDENTIALS_JSON"))

scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_dict(GOOGLE_CREDENTIALS_JSON, scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

def get_user(email):
    users = sheet.worksheet("Usuarios").get_all_records()
    for u in users:
        if u['email'] == email and u['estado'] == 'activo':
            return u
    return None

@app.route("/")
def login():
    return render_template_string("""
    <form method="post" action="/login">
        Email: <input name="email"><br>
        Password: <input name="password" type="password"><br>
        <button>Entrar</button>
    </form>""")

@app.route("/login", methods=["POST"])
def login_post():
    email = request.form['email']
    password = request.form['password']
    user = get_user(email)
    if user and user['password'] == password:
        session['user'] = user
        return f"Bienvenido {user['nombre']} - Rol: {user['rol']}"
    return "Login invalido"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
