from flask import Flask, render_template, request, redirect, url_for
import re
import os
from urllib.parse import urlparse
from pg8000.native import Connection, DatabaseError

app = Flask(__name__)

# =================================================================
# CONFIGURACIÓN Y CONEXIÓN A POSTGRESQL
# =================================================================
def obtener_conexion_db():
    """Detecta el entorno y extrae los parámetros directamente de la URL."""
    cadena_conexion = os.environ.get('DATABASE_URL') or "postgresql://sena_t4sc_user:BRtyaeq8r7Jc7AKTlgRGrhN4Qiv2g1BF@dpg-d8f3fdurnols73am6030-a.oregon-postgres.render.com/sena_t4sc"
    
    url = urlparse(cadena_conexion)
    
    username = url.username
    password = url.password
    host = url.hostname
    port = url.port or 5432
    database = url.path.lstrip('/')
    
    return Connection(
        user=username,
        password=password,
        host=host,
        port=port,
        database=database,
        timeout=15
    )

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

def consultar_estudiantes(conn, criterio=None):
    """Consulta usando 'documentoc' y mapea manualmente por posición para evitar fallos de dict()."""
    try:
        if criterio:
            query = """
                SELECT documentoc, nombre, correo, programa, ficha 
                FROM estudiantes 
                WHERE LOWER(documentoc) LIKE :1 OR LOWER(nombre) LIKE :2
                ORDER BY id DESC
            """
            valor_busqueda = f"%{criterio}%"
            resultado = conn.run(query, valor_busqueda, valor_busqueda)
        else:
            query = "SELECT documentoc, nombre, correo, programa, ficha FROM estudiantes ORDER BY id DESC"
            resultado = conn.run(query)
        
        if not resultado:
            return []
            
        estudiantes = []
        for fila in resultado:
            # LÓGICA ESTRICTA: Solo procesamos si es una tupla/lista con los 5 campos de datos reales
            if isinstance(fila, (list, tuple)) and len(fila) == 5:
                estudiantes.append({
                    'documento': str(fila[0]),
                    'nombre': str(fila[1]),
                    'correo': str(fila[2]),
                    'programa': str(fila[3]),
                    'ficha': str(fila[4])
                })
                
        return estudiantes
    except Exception:
        return []

# ==========================================
# VISTA 1: CONTROL DE ESTUDIANTES (RAÍZ)
# ==========================================
@app.route("/", methods=["GET"])
def index():
    criterio = request.args.get('buscar', '').strip().lower()
    
    try:
        conn = obtener_conexion_db()
        estudiantes_visibles = consultar_estudiantes(conn, criterio)
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
        
        error = validar_datos(datos_formulario)
        conn = obtener_conexion_db()
        
        if error:
            estudiantes_actuales = consultar_estudiantes(conn)
            return render_template("index.html", estudiantes=estudiantes_actuales, error_validacion=error, busqueda_actual="")
        
        # Validación de duplicados apuntando a 'documentoc'
        existe = conn.run("SELECT id FROM estudiantes WHERE documentoc = :1 OR correo = :2", 
                          datos_formulario['documento'], datos_formulario['correo'])
        if && existe and isinstance(existe, (list, tuple)) and len(existe) > 0 and len(existe[0]) > 0:
            estudiantes_actuales = consultar_estudiantes(conn)
            return render_template("index.html", estudiantes=estudiantes_actuales, error_validacion="El documento o correo ya existen.", busqueda_actual="")

        # Inserción apuntando a 'documentoc'
        query = """
            INSERT INTO estudiantes (documentoc, nombre, correo, programa, ficha) 
            VALUES (:1, :2, :3, :4, :5)
        """
        conn.run(query, 
                 datos_formulario['documento'],
                 datos_formulario['nombre'],
                 datos_formulario['correo'],
                 datos_formulario['programa'],
                 datos_formulario['ficha'])
        
        return redirect(url_for('index'))
        
    except Exception as e:
        return f"""
        <div style="background-color: #ffe6e6; padding: 25px; border: 3px solid #ff3333; font-family: monospace; margin: 50px auto; max-width: 800px; border-radius: 8px;">
            <h2 style="color: #cc0000; margin-top: 0;">⚠️ Error al registrar</h2>
            <p><strong>Mensaje técnico real:</strong> {str(e)}</p>
        </div>
        """, 500

@app.route("/limpiar")
def limpiar():
    try:
        conn = obtener_conexion_db()
        conn.run("TRUNCATE TABLE estudiantes RESTART IDENTITY CASCADE;")
    except Exception as e:
        return f"Error al limpiar la base de datos: {str(e)}", 500
        
    return redirect(url_for('index'))

@app.route("/juego")
def juego():
    return render_template("juegos.html")

if __name__ == "__main__":
    app.run(debug=True)