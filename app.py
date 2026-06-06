from flask import Flask, render_template, request, redirect, url_for
import re

app = Flask(__name__)

# Base de datos temporal en memoria
LISTA_ESTUDIANTES = []

def validar_datos(datos):
    """Función auxiliar para validar los campos del formulario"""
    if not all(str(valor).strip() for valor in datos.values()):
        return "Todos los campos son obligatorios y no pueden contener solo espacios."
    if not re.match(r"^\d{6,12}$", datos['documento']):
        return "El documento de identidad debe ser un número válido entre 6 and 12 dígitos."
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$", datos['nombre']):
        return "El nombre completo solo debe contener letras."
    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", datos['correo']):
        return "El correo electrónico introducido no tiene un formato válido."
    if not re.match(r"^\d{5,8}$", datos['ficha']):
        return "El número de ficha debe contener únicamente entre 5 and 8 números."
    return None

@app.route("/", methods=["GET"])
def index():
    # Capturar el texto del filtro de búsqueda (?buscar=texto)
    criterio = request.args.get('buscar', '').strip().lower()
    
    # Punto 3: Consultar estudiantes (Filtrados o Completos)
    if criterio:
        # Filtra si el criterio coincide con el documento O con el nombre del alumno
        estudiantes_visibles = [
            est for est in LISTA_ESTUDIANTES 
            if criterio in est['documento'].lower() or criterio in est['nombre'].lower()
        ]
    else:
        # Si no hay búsqueda, se muestran todos de forma nativa
        estudiantes_visibles = LISTA_ESTUDIANTES

    return render_template(
        "index.html", 
        estudiantes=estudiantes_visibles, 
        busqueda_actual=request.args.get('buscar', ''), # Mantiene el texto en el input
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

if __name__ == "__main__":
    app.run(debug=True)