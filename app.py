from flask import Flask, request
import pandas as pd

app = Flask(__name__)

# Cargamos la base de datos
datos = pd.read_csv('datos.csv')

def buscar_puntaje(cc):
    resultado = datos[datos['CC'] == int(cc)]
    if not resultado.empty:
        fila = resultado.iloc[0]
        return f"<h2 style='color:green'>Nombre: {fila['Nombre']}</h2><h2>Puntaje: {fila['Puntaje']}</h2><h2>Estado: {fila['Estado']}</h2>"
    else:
        return "<h2 style='color:red'>CC no encontrada</h2>"

@app.route('/', methods=['GET', 'POST'])
def inicio():
    resultado = ""
    if request.method == 'POST':
        cc = request.form.get('cc')
        resultado = buscar_puntaje(cc)

    return f"""
    <style>
    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f0f2f5; }}
   .caja {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
    input {{ padding: 10px; width: 200px; border: 1px solid #ccc; border-radius: 5px; }}
    button {{ padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; }}
    h1 {{ color: #2563eb; }}
    </style>
    <div class="caja">
        <h1>ArriendoScore.co</h1>
        <p>El Datacredito de Arriendos en Colombia</p>
        <form method="POST">
            <input name="cc" placeholder="Ingresa la CC" required>
            <button>Consultar</button>
        </form>
        {resultado}
    </div>
    """

if __name__ == '__main__':
    app.run()
