from flask import Flask, request
import pandas as pd
import os

app = Flask(__name__)
ruta = os.path.join(os.path.dirname(__file__), 'datos.csv')
datos = pd.read_csv(ruta)

@app.route('/', methods=['GET', 'POST'])
def inicio():
    resultado = ""
    if request.method == 'POST':
        cc = request.form.get('cc')
        fila = datos[datos.iloc[:, 0].astype(str) == str(cc)]
        if not fila.empty:
            fila = fila.iloc[0]
            resultado = "<div style='background:#f0f9ff;padding:20px;border-radius:10px;margin-top:20px;border-left:4px solid #0284c7'>"
            resultado += f"<h3 style='color:green'>✅ Encontrado</h3>"
            resultado += f"<p><b>Nombre:</b> {fila.iloc[1]}</p>"
            resultado += f"<p><b>Puntaje:</b> {fila.iloc[2]}</p>"
            resultado += f"<p><b>Estado:</b> {fila.iloc[3]}</p>"
            resultado += "</div>"
        else:
            resultado = "<p style='color:red'>❌ CC no encontrada</p>"

    return """
    <style>
    body { font-family: 'Segoe UI', sans-serif; background: linear-gradient(135deg, #0ea5e9, #0284c7); padding: 50px; }
   .caja { background: white; padding: 40px; border-radius: 15px; max-width: 600px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
    h1 { color: #0284c7; font-size: 36px; margin:0 }
   .slogan { color:#666; margin-bottom:25px }
    </style>
    <div class="caja">
        <h1>📊 DatoArriendo.co</h1>
        <p class="slogan">El Datacredito de Arrendatarios en Colombia</p>
        <form method="POST">
            <input name="cc" placeholder="Ingresa número de CC" required style="padding:12px; width: 250px; border:2px solid #ddd; border-radius:8px">
            <button style="padding:12px 24px; background:#0284c7; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold">Consultar</button>
        </form>
    """ + resultado + """
    </div>
    """
