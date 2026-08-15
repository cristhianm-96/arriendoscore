import pandas as pd
from flask import Flask, render_template_string, request

app = Flask(__name__)

# Cargar datos
try:
    df = pd.read_csv("datos.csv")
    df.columns = df.columns.str.strip().str.lower() # para que no falle por mayúsculas
except Exception as e:
    print("Error cargando datos:", e)
    df = pd.DataFrame()

HTML = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ArriendoScore.co - El Datacrédito de Arriendos</title>
<style>
    body { font-family: Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 40px 20px; display: flex; justify-content: center; }
  .card-principal { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 500px; width: 100%; text-align: center; }
    h1 { color: #0056b3; margin: 0; font-size: 32px; }
   .sub { color: #555; margin-bottom: 20px; }
  .logo { width: 160px; margin-bottom: 15px; }
   .buscador { display: flex; gap: 10px; margin-bottom: 20px; }
   .buscador input { flex: 1; padding: 12px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
   .buscador button { padding: 12px 20px; background: #0056b3; color: white; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; }
   .buscador button:hover { background: #003d82; }
   .resultado { margin-top: 20px; text-align: left; }
  .encontrado { color: #28a745; font-weight: bold; font-size: 20px; display: flex; align-items: center; justify-content: center; gap: 8px; }
  .no-encontrado { color: #dc3545; font-weight: bold; font-size: 20px; }
   .dato { margin: 8px 0; }
   .dato b { color: #333; }
</style>
</head>
<body>
    <div class="card-principal">
        <img src="/static/logo.jpeg" class="logo" alt="ArriendoScore">
        <h1>DatoArriendo</h1>
        
        <form method="POST" class="buscador">
            <input type="text" name="cc" placeholder="Ingresa la CC" required>
            <button type="submit">Consultar</button>
        </form>

        {% if resultado %}
        <div class="resultado">
            {% if resultado.encontrado %}
                <p class="encontrado">✅ Encontrado</p>
                <p class="dato"><b>Nombre:</b> {{ resultado.nombre }}</p>
                <p class="dato"><b>Puntaje:</b> {{ resultado.puntuación }}</p>
                <p class="dato"><b>Estado:</b> {{ resultado.estado }}</p>
                <p class="dato"><b>Reportes:</b> {{ resultado.informes }}</p>
            {% else %}
                <p class="no-encontrado">❌ No encontrado</p>
                <p>Esta persona no tiene historial en ArriendoScore</p>
            {% endif %}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    resultado = None
    if request.method == "POST":
        cc_buscar = request.form["cc"].strip()
        persona = df[df['cc'].astype(str) == cc_buscar]
        if not persona.empty:
            resultado = persona.iloc[0].to_dict()
            resultado['encontrado'] = True
        else:
            resultado = {'encontrado': False}
    
    return render_template_string(HTML, resultado=resultado)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
