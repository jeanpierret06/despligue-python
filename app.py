from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Base de datos temporal en memoria (compartida por todos los usuarios)
LISTA_ESTUDIANTES = []

@app.route("/", methods=["GET"])
def index():
    # Muestra la página de inicio junto con los estudiantes guardados
    return render_template("index.html", estudiantes=LISTA_ESTUDIANTES)

@app.route("/registrar", methods=["POST"])
def registrar():
    # Captura los datos del formulario
    nuevo_estudiante = {
        'documento': request.form.get('documento'),
        'nombre': request.form.get('nombre'),
        'correo': request.form.get('correo'),
        'programa': request.form.get('programa'),
        'ficha': request.form.get('ficha')
    }
    
    # Valida que no se envíen campos vacíos antes de guardar
    if all(nuevo_estudiante.values()):
        LISTA_ESTUDIANTES.append(nuevo_estudiante)
        
    return redirect(url_for('index'))

@app.route("/limpiar")
def limpiar():
    # Vacía la lista por completo
    LISTA_ESTUDIANTES.clear()
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)