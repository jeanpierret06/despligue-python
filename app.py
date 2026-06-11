import os
import re
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN DE POSTGRESQL (SQLALCHEMY)
# ==========================================
DATABASE_URL = os.environ.get('DATABASE_URL')

if DATABASE_URL:
    # 1. Corregir el prefijo obsoleto 'postgres://' si Render lo llega a enviar así
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    # 2. Si no detecta la variable de entorno (por ejemplo, corriendo en tu PC local), 
    # usamos la URL externa de Render añadiéndole el dominio para que se conecte desde afuera.
    DATABASE_URL = "postgresql://sena_t4sc_user:BRtyaeq8r7Jc7AKTlgRGrhN4Qiv2g1BF@dpg-d8f3fdurnols73am6030-a.render.com/sena_t4sc"

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==========================================
# MODELO DE LA BASE DE DATOS
# ==========================================
class Estudiante(db.Model):
    __tablename__ = 'estudiantes'
    
    id = db.Column(db.Integer, primary_key=True)
    documento = db.Column(db.String(12), unique=True, nullable=False)
    nombre = db.Column(db.String(150), nullable=False)
    correo = db.Column(db.String(150), unique=True, nullable=False)
    programa = db.Column(db.String(100), nullable=False)
    ficha = db.Column(db.String(8), nullable=False)

    def to_dict(self):
        """Método auxiliar para mantener compatibilidad si tus vistas HTML usan sintaxis de diccionario"""
        return {
            'documento': self.documento,
            'nombre': self.nombre,
            'correo': self.correo,
            'programa': self.programa,
            'ficha': self.ficha
        }

# Generar automáticamente las tablas en PostgreSQL si no existen al iniciar la aplicación
with app.app_context():
    db.create_all()


# ==========================================
# LOGICA DE VALIDACIÓN
# ==========================================
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
    criterio = request.args.get('buscar', '').strip()
    
    # Lógica de consulta a PostgreSQL usando operadores LIKE
    if criterio:
        resultados_db = Estudiante.query.filter(
            (Estudiante.documento.ilike(f"%{criterio}%")) | 
            (Estudiante.nombre.ilike(f"%{criterio}%"))
        ).all()
    else:
        resultados_db = Estudiante.query.all()

    # Convertimos los objetos de la BD a una lista de diccionarios para no romper tus plantillas HTML existentes
    estudiantes_visibles = [est.to_dict() for est in resultados_db]

    return render_template(
        "index.html", 
        estudiantes=estudiantes_visibles, 
        busqueda_actual=criterio,
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
            # Si hay error de formato, recuperamos los estudiantes actuales para recargar la vista correctamente
            todos = [est.to_dict() for est in Estudiante.query.all()]
            return render_template("index.html", estudiantes=todos, error_validacion=error, busqueda_actual="")
        
        # Validar si el documento o correo ya existen en la base de datos para evitar errores de duplicidad catastróficos
        estudiante_existente = Estudiante.query.filter(
            (Estudiante.documento == datos_formulario['documento']) | 
            (Estudiante.correo == datos_formulario['correo'])
        ).first()
        
        if estudiante_existente:
            todos = [est.to_dict() for est in Estudiante.query.all()]
            return render_template("index.html", estudiantes=todos, error_validacion="El documento o el correo ya se encuentran registrados.", busqueda_actual="")

        # Lógica de inserción en PostgreSQL
        nuevo_estudiante = Estudiante(
            documento=datos_formulario['documento'],
            nombre=datos_formulario['nombre'],
            correo=datos_formulario['correo'],
            programa=datos_formulario['programa'],
            ficha=datos_formulario['ficha']
        )
        db.session.add(nuevo_estudiante)
        db.session.commit() # Guardar cambios en la nube
        
        return redirect(url_for('index'))
        
    except Exception as e:
        db.session.rollback() # Revierte la transacción si algo sale mal
        return render_template("error.html", error=str(e)), 500

@app.route("/limpiar")
def limpiar():
    try:
        # Lógica para vaciar la tabla completamente en PostgreSQL
        db.session.query(Estudiante).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
    return redirect(url_for('index'))


# ==========================================
# VISTA 2: RUTA DEL JUEGO INTERACTIVO
# ==========================================
@app.route("/juego")
def juego():
    return render_template("juegos.html")

if __name__ == "__main__":
    app.run(debug=True)