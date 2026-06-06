from flask import Flask, render_template, request, redirect, url_for
import re

app = Flask(__name__)

LISTA_ESTUDIANTES = []

def validar_datos(datos):
    if not all(str(valor).strip() for valor in datos.values()):
        return "Todos los campos son obligatorios."
    if not re.match(r"^\d{6,12}$", datos['documento']):
        return "El documento debe ser numérico (6-12 dígitos)."
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", datos['nombre']):
        return "El nombre completo solo debe contener letras."
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", datos['correo']):
        return "Formato de correo electrónico inválido."
    if not re.match(r"^\d{5,8}$", datos['ficha']):
        return "La ficha debe ser numérica (5-8 dígitos)."
    return None

# ==========================================
# VISTA 1: CONTROL DE ESTUDIANTES (RAÍZ)
# ==========================================
@app.route("/", methods=["GET"])
def index():
    criterio = request.args.get('buscar', '').strip().lower()
    if criterio:
        estudiantes_visibles = [
            est for est in LISTA_ESTUDIANTES 
            if criterio in est['documento'].lower() or criterio in est['nombre'].lower()
        ]
    else:
        estudiantes_visibles = LISTA_ESTUDIANTES

    return render_template(
        "index.html", 
        estudiantes=estudiantes_visibles, 
        busqueda_actual=request.args.get('buscar', ''),
        error_validacion=None
    )

@app.route("/registrar", methods=["POST"])
def registrar():
    try:
        datos_formulario = {
            'documento': request.form.get('documento', '').strip(),
            'nombre': request.form.get('nombre', '').strip(),
            'correo': request.form.get('correo', '').strip(),
            'programa': request.form.get('programa', '').strip(),
            'ficha': request.form.get('ficha', '').strip()
        }
        error = validar_datos(datos_formulario)
        if error:
            return render_template("index.html", estudiantes=LISTA_ESTUDIANTES, error_validacion=error, busqueda_actual="")
        LISTA_ESTUDIANTES.append(datos_formulario)
        return redirect(url_for('index'))
    except Exception as e:
        return render_template("error.html", error=str(e)), 500

@app.route("/limpiar")
def limpiar():
    LISTA_ESTUDIANTES.clear()
    return redirect(url_for('index'))


# ==========================================
# VISTA 2: RUTA DEL JUEGO INTERACTIVO
# ==========================================
@app.route("/juego")
def juego():
    # Renderiza directamente el entorno gráfico interactivo de JavaScript
    return render_template("juego.html")

if __name__ == "__main__":
    app.run(debug=True)