from flask import Flask, render_template, request, redirect, url_for
import re
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# ==========================================
# CONFIGURACIÓN Y CONEXIÓN A POSTGRESQL
# ==========================================
# Reemplaza los valores de abajo con tus credenciales de Aiven/PostgreSQL si pruebas localmente.
# En Render, se recomienda crear una Variable de Entorno llamada DATABASE_URL.
DATABASE_URL = os.environ.get('DATABASE_URL') or "postgresql://usuario:contraseña@host:puerto/nombre_bd"

def obtener_conexion_db():
    """Establece y retorna la conexión física con la base de datos PostgreSQL."""
    # Usamos RealDictCursor para que los resultados actúen como diccionarios, igual que tu lista antigua
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

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
    
    try:
        conn = obtener_conexion_db()
        cursor = conn.cursor()
        
        if criterio:
            # Consulta SQL con filtros de búsqueda parcial (LIKE) insensible a mayúsculas/minúsculas
            query = """
                SELECT documento, nombre, correo, programa, ficha 
                FROM estudiantes 
                WHERE LOWER(documento) LIKE %s OR LOWER(nombre) LIKE %s
                ORDER BY id DESC
            """
            valor_busqueda = f"%{criterio}%"
            cursor.execute(query, (valor_busqueda, valor_busqueda))
        else:
            # Traer todos los alumnos matriculados
            query = "SELECT documento, nombre, correo, programa, ficha FROM estudiantes ORDER BY id DESC"
            cursor.execute(query)
            
        estudiantes_visibles = cursor.fetchall()
        cursor.close()
        conn.close()
        
    except Exception as e:
        return f"Error de conexión a la base de datos: {str(e)}", 500

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
        
        # Validaciones de expresiones regulares
        error = validar_datos(datos_formulario)
        if error:
            # Si hay error de formato, recuperamos los estudiantes actuales para no romper la vista
            conn = obtener_conexion_db()
            cursor = conn.cursor()
            cursor.execute("SELECT documento, nombre, correo, programa, ficha FROM estudiantes ORDER BY id DESC")
            estudiantes_actuales = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return render_template("index.html", estudiantes=estudiantes_actuales, error_validacion=error, busqueda_actual="")
        
        # Inserción persistente en PostgreSQL
        conn = obtener_conexion_db()
        cursor = conn.cursor()
        
        # Comprobar primero si el documento o correo ya existen para evitar caídas por restricciones UNIQUE
        cursor.execute("SELECT id FROM estudiantes WHERE documento = %s OR correo = %s", 
                       (datos_formulario['documento'], datos_formulario['correo']))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return "El documento o el correo electrónico ya se encuentran registrados.", 400

        query = """
            INSERT INTO estudiantes (documento, nombre, correo, programa, ficha) 
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            datos_formulario['documento'],
            datos_formulario['nombre'],
            datos_formulario['correo'],
            datos_formulario['programa'],
            datos_formulario['ficha']
        ))
        
        # Guardar físicamente los datos en el disco duro de PostgreSQL
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return redirect(url_for('index'))
        
    except Exception as e:
        return render_template("error.html", error=str(e)), 500

@app.route("/limpiar")
def limpiar():
    try:
        conn = obtener_conexion_db()
        cursor = conn.cursor()
        
        # Vacía la tabla por completo reinstanciando los contadores SERIAL
        cursor.execute("TRUNCATE TABLE estudiantes RESTART IDENTITY CASCADE;")
        conn.commit()
        
        cursor.close()
        conn.close()
    except Exception as e:
        return f"Error al limpiar la base de datos: {str(e)}", 500
        
    return redirect(url_for('index'))


# ==========================================
# VISTA 2: RUTA DEL JUEGO INTERACTIVO
# ==========================================
@app.route("/juego")
def juego():
    return render_template("juegos.html")

if __name__ == "__main__":
    app.run(debug=True)