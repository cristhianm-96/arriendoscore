import pandas as pd
from flask import Flask, render_template_string

app = Flask(__name__)

# Cargar datos
try:
    df = pd.read_csv("datos.csv")
    df["Precio"] = pd.to_numeric(df["Precio"], errors='coerce')
    df["Barrio"] = df["Barrio"].astype(str)
except Exception as e:
    print("Error cargando datos:", e)
    df = pd.DataFrame()

# HTML con el logo en /static/logo.jpeg
HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>DatoArriendo - Busca tu arriendo ideal</title>
<style>
    body { font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 0; }
    header { background: #0056b3; color: white; padding: 15px; text-align: center; }
    .logo { width: 180px; margin-bottom: 10px; }
    h1 { margin: 0; font-size: 24px; }
    .container { padding: 20px; max-width: 900px; margin: auto; }
    .card { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .precio { color: #0056b3; font-weight: bold; font-size: 18px; }
    footer { text-align: center; padding: 15px; background: #eee; margin-top: 20px; }
</style>
</head>
<body>
    <header>
        <img src="/static/logo.jpeg" class="logo" alt="DatoArriendo">
        <h1>Encuentra tu próximo arriendo en Bogotá</h1>
    </header>
    <div class="container">
        {% for i, row in datos.iterrows() %}
        <div class="card">
            <h2>{{ row['Barrio'] }}</h2>
            <p class="precio">${{ "{:,.0f}".format(row['Precio']) }} COP</p>
            <p><b>Habitaciones:</b> {{ row['Habitaciones'] }} | <b>Baños:</b> {{ row['Baños'] }}</p>
            <p><b>Área:</b> {{ row['Área'] }} m²</p>
        </div>
        {% endfor %}
    </div>
    <footer>
        <p>© 2026 DatoArriendo - Datos actualizados</p>
    </footer>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML, datos=df)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
