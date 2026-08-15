from flask import Flask, request
import pandas as pd
import os

app = Flask(__name__)

# Cargar los datos del CSV
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
            resultado = "<div style='background:#f0f9ff;padding:20px;border-radius:10px;margin-top:20px;border-left:4px solid #2563eb; text-align:left'>"
            resultado += f"<h3 style='color:#16a34a; margin-top:0'>✅ Encontrado</h3>"
            resultado += f"<p><b>Nombre:</b> {fila.iloc[1]}</p>"
            resultado += f"<p><b>Puntaje:</b> {fila.iloc[2]}</p>"
            resultado += f"<p><b>Estado:</b> {fila.iloc[3]}</p>"
            resultado += "</div>"
        else:
            resultado = "<p style='color:red; margin-top:20px'>❌ CC no encontrada</p>"

    return """
    <style>
    body { 
        font-family: 'Segoe UI', sans-serif; 
        background: linear-gradient(135deg, #2563eb, #1e40af); 
        padding: 50px; 
        margin: 0;
    }
   .caja { 
        background: white; 
        padding: 40px; 
        border-radius: 15px; 
        max-width: 600px; 
        margin: auto; 
        box-shadow: 0 10px 30px rgba(0,0,0,0.2); 
        text-align:center 
    }
   .logo { 
        width:120px; 
        margin-bottom:10px 
    }
    h1 { 
        color: #1e40af; 
        font-size: 28px; 
        margin:10px 0 
    }
   .slogan { 
        color:#666; 
        margin-bottom:25px; 
        font-size:14px 
    }
    input { 
        padding:12px; 
        width: 60%; 
        border:2px solid #ddd; 
        border-radius:8px;
        font-size:16px;
    }
    button { 
        padding:12px 24px; 
        background:#2563eb; 
        color:white; 
        border:none; 
        border-radius:8px; 
        cursor:pointer; 
        font-weight:bold; 
        margin-top:10px;
        font-size:16px;
    }
    button:hover {
        background:#1e40af;
    }
    </style>
    <div class="caja">
        <img src="logo.jpeg" class="logo" alt="DatoArriendo">
        <h1>DatoArriendo</h1>
        <p class="slogan">El Datacrédito de los Arrendatarios</p>
        <form method="POST">
            <input name="cc" placeholder="Ingresa número de CC" required>
            <br>
            <button>Consultar</button>
        </form>
    """ + resultado + """
    </div>
    """

if __name__ == '__main__':
    app.run(debug=True)
