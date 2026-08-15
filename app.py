from flask import Flask, request
import pandas as pd
import os

app = Flask(__name__)

# Cargamos el CSV
ruta = os.path.join(os.path.dirname(__file__), 'datos.csv')
datos = pd.read_csv(ruta)

@app.route('/', methods=['GET', 'POST'])
def inicio():
    resultado = ""
    if request.method == 'POST':
        cc = request.form.get('cc')
        # Buscamos en columna 0 = cc
        fila = datos[datos.iloc[:, 0].astype(str) == str(cc)]
        if not fila.empty:
            fila = fila.iloc[0]
            resultado = f"""
            <h2 style='color:green'>✅ Encontrado</h2>
            <p><b>Nombre:</b> {fila.iloc[1]}</p>
            <p><b>Puntaje:</b> {fila.iloc[2]}</p>
            <p><b>Estado:</b> {fila.iloc[3]}</p>
            <p><b>Reportes:</b> {fila.iloc[4]}</p>
            """
        else:
            resultado = "<h2 style='color:red'>❌ CC no encontrada</h2>"

    return f"""
    <style>
    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f0f2f5; }}
   .caja {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
    input {{ padding: 12px; width: 220px; border: 1px solid #ccc; border-radius: 5px; font-size:16px }}
    button {{ padding: 12px 24px; background: #2563eb; color: white; border: none; border-radius: 5px; font-size:16px; cursor: pointer; }}
    h1 {{ color: #2563eb; }}
    </style>
    <div class="caja">
        <h1>datoarriendo</h1>
        <p>El Datacredito de Arriendos en Colombia</p>
        <form method="POST">
            <input name="cc" placeholder="Ingresa la CC" required>
            <button>Consultar</button>
        </form>
        <div style="margin-top:20px">{resultado}</div>
    </div>
    """
