    from flask import Flask

    app = Flask(__name__)

    @app.route('/')
    def inicio():
        resultado = ""
        return f"""
        <style>
        body {{ font-family: Arial; text-align: center; padding: 50px; background: #f0f2f5; }}
        .caja {{ background: white; padding: 30px; border-radius: 10px; max-width: 500px; margin: auto; }}
        input {{ padding: 10px; width: 200px; border: 1px solid #ccc; }}
        button {{ padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 5px; }}
        h1 {{ color: #2563eb; }}
        </style>
        <div class="caja">
          <h1>ArriendoScore.co</h1>
          <p>El Datacredito de Arriendos en Colombia</p>
          <form method="POST">
            <input name="cc" placeholder="Ingresa la CC">
            <button>Consultar</button>
          </form>
          <h2>{resultado}</h2>
        </div>
        """
