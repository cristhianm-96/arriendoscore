from flask import Flask, request

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def inicio():
    resultado = ""
    if request.method == 'POST':
        cc = request.form.get('cc')
        resultado = f"Consultaste la CC: {cc}. Aquí irá el puntaje."

    return f"""
    <style>
    body {{ font-family: Arial; text-align: center; padding: 50px; background: #f0f2f5; }}
    .caja {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }}
    input {{ padding: 10px; width: 200px; border: 1px solid #ccc; border-radius: 5px; }}
    button {{ padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; }}
    h1 {{ color: #2563eb; }}
    h2 {{ color: #16a34a; }}
    </style>
    <div class="caja">
      <h1>ArriendoScore.co</h1>
      <p>El Datacredito de Arriendos en Colombia</p>
      <form method="POST">
        <input name="cc" placeholder="Ingresa la CC" required>
        <button>Consultar</button>
      </form>
      <h2>{resultado}</h2>
    </div>
    """
    
