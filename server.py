from flask import Flask, render_template, request, flash, url_for, redirect
from consolex import console
from dotenv import load_dotenv
import re
import pymysql
import os

import pymysql

load_dotenv()



app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

ALLOWED_TABLES = ("productos", "usuario")

def get_db_connection():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        db=os.getenv("MYSQL_DB"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        unix_socket=os.getenv("MYSQL_UNIX_SOCKET"),
        cursorclass=pymysql.cursors.DictCursor
    )

def updatesql(tabla, id_column, id_valor, data, allowed_columns = None):
    if not data:
        flash("Datos no ingresados", "danger")
        return False
    if allowed_columns:
        data= {k: v for k, v in data.items() if k in allowed_columns}
    values = list(data.values())

    set_clause = ", ". join([f"{col} = %s" for col in data.keys()])
    values = list(data.values())

    sql= f"UPDATE {tabla} SET {set_clause} WHERE {id_column} = %s"
    values.append(id_valor)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()
    return 


def validar_longitud(texto, min_len, max_len):
    return min_len <= len(texto) <= max_len

def ValidarCampo(valor, tipo_campo):
    if not valor:
        flash("El campo no puede estar vacío", "danger")
        return False

    if tipo_campo == "cNombre" or tipo_campo == "cApellp" or tipo_campo == "cApellm":
        patron = re.compile(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ]+(?:\s+[A-Za-zÁÉÍÓÚáéíóúÑñ]+)*$')
        if not patron.match(valor.strip()):
            match tipo_campo:
                case "cNombre":
                    if not validar_longitud(valor, 2,50):
                        flash("Error: el nombre o apellidos no es válido", "danger")
                    return False
                case "cApellp":
                    if not validar_longitud(valor, 2,150):
                        flash("Error: el nombre o apellidos no es válido", "danger")
                    return False
                case "cApellm":
                    if not validar_longitud(valor, 2,150):
                        flash("Error: el apellido materno no es válido", "danger")
                    return False
        else:
            return True
    elif tipo_campo == "cEmail":
        patron = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not patron.match(valor.strip()):
            flash("Error: el email no es valido","danger")
            return False
    elif tipo_campo == "cContrasena":
        if len(valor) < 6:
            flash("Error: el contraseña no es valido","danger")
            return False
    elif tipo_campo == "cEdad":
        try:
            edad_int = int(valor)
            if edad_int < 0 or edad_int > 120:
                flash("Error: la edad no es valida","danger")
                return False
        except ValueError: 
            flash("Error: la edad debe ser un numero entero", "danger")
            return False
    else:
        return console.log("Tipo de campo no reconocido para validacion")

    return True

def todosCampos(vnom,vapellp,vapellm,vemail,vcontra,vedad):
    
    if not vnom or not vapellp or not vapellm or not vemail or not vcontra or not vedad:
        flash("Error: los datos no son validos","danger")
        return False
    else:
        return True

@app.route('/')
def index():
    return render_template("index.html")

def busqueda(tabla,columna, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    sql = f"SELECT * FROM {tabla} WHERE {columna} = %s"

    cursor.execute(sql, (id,))
    usuario = cursor.fetchall()

    cursor.close()
    conn.close()
    return usuario

def deletesql(tabla,columna, id):
        
        try:

            conn = get_db_connection()
            cursor = conn.cursor()
            sql = f"DELETE FROM {tabla} WHERE {columna} = %s"

            cursor.execute(sql, (id,))
            conn.commit()  # 🔥 IMPORTANTE

            affected = cursor.rowcount

            cursor.close()
            conn.close()

            return affected > 0

        except Exception as e:
            print("Error en DELETE:", e)

            try:
                conn.rollback()
            except:
                pass

            return False

def insertsql(tabla, data, allowed_columns=None):
    try:
        if not data:
            flash("Datos no ingresados", "danger")
            return False
        if tabla not in ALLOWED_TABLES:
            raise ValueError("Tabla no permitida")
        if allowed_columns:
            data = {k: v for k, v in data.items() if k in allowed_columns}

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        values = list(data.values())

        sql = f"INSERT INTO {tabla} ({columns}) VALUES ({placeholders})"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(sql, values)
        conn.commit()
        cursor.close()
        conn.close()

        return True
    except Exception as e:
            print("Error en INSERT INTO:", e)

            try:
                conn.rollback()
            except:
                pass

            return False


@app.route('/formulario', methods=["GET", "POST"])
def formulario():

    if request.method == "POST":
        nombre = request.form.get('cNombre')
        apellp = request.form.get('cApellp')
        apellm = request.form.get('cApellm')
        email = request.form.get('cEmail')
        contrasena = request.form.get('cContrasena')
        edad = request.form.get('cEdad')
        ctyc = request.form.get('cTyc')

        validacion_nombre = ValidarCampo(nombre, "cNombre")
        validacion_apellp = ValidarCampo(apellp, "cApellp")
        validacion_apellm = ValidarCampo(apellm, "cApellm")
        validacion_email = ValidarCampo(email, "cEmail")
        validacion_contrasena = ValidarCampo(contrasena, "cContrasena")
        validacion_edad = ValidarCampo(edad, "cEdad")
        
        todosCamposOK = todosCampos(validacion_nombre, validacion_apellp,validacion_apellm,validacion_email,validacion_contrasena,validacion_edad)
        print(request.form)
        if ctyc != "ok":
            flash("Error: Debe aceptar terminos y condiciones")
            return render_template("formulario.html")
        elif not todosCamposOK:
            flash("Error: Debe completar todos los campos")
            return render_template("formulario.html")
        data = {
            "name_user": nombre,
            "apell_user": apellp,
            "apellm_user": apellm,
            "mail_user": email,
            "contra_user": contrasena,
            "edad_user": edad
        }

        resultado = insertsql(
            tabla="usuario",
            data=data,
            allowed_columns={"name_user", "apell_user", "apellm_user", "edad_user", "mail_user", "contra_user"}
        )

        if resultado:
            flash("¡Formulario válido y guardado!", "success")
        else:
            flash("Error al guardar en la base de datos", "danger")

        return render_template("formulario.html")

    return render_template("formulario.html")


@app.route('/tabla', methods=["GET"])
def tabla():


    busqueda = request.args.get('busqueda', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    if busqueda: 
        sql = """
        SELECT * FROM usuario
        WHERE name_user LIKE %s OR CAST(id_user AS CHAR) = %s
        """
        valores = (f"%{busqueda}%", busqueda)
        cursor.execute(sql, valores)
    else: 
        sql = "SELECT * FROM usuario"
        cursor.execute(sql)

    usuarios = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("tabla.html", usuarios=usuarios, queda=busqueda)

@app.route('/editar/<int:id_user>', methods=["GET", "POST"])
def editar(id_user):
    usuario = busqueda("usuario", "id_user", id_user)
    usuario = usuario[0] if usuario else None

    if request.method == "POST":

        nombre = request.form.get('eNombre')
        apellp = request.form.get('eApellp')
        apellm = request.form.get('eApellm')
        email = request.form.get('eEmail')
        contrasena = request.form.get('eContrasena')
        edad = request.form.get('eEdad')

        validacion_nombre = ValidarCampo(nombre, "cNombre")
        validacion_apellp = ValidarCampo(apellp, "cApellp")
        validacion_apellm = ValidarCampo(apellm, "cApellm")
        validacion_email = ValidarCampo(email, "cEmail")
        validacion_contrasena = ValidarCampo(contrasena, "cContrasena")
        validacion_edad = ValidarCampo(edad, "cEdad")
        print("NOMBRE:", nombre)
        print("APELLP:", apellp)
        print("APELLM:", apellm)
        print("EMAIL:", email)
        todosCamposOK = todosCampos(
            validacion_nombre,
            validacion_apellp,
            validacion_apellm,
            validacion_email,
            validacion_contrasena,
            validacion_edad
        )

        if not todosCamposOK:
            flash("Error: Debe completar todos los campos", "danger")
            return redirect(url_for('editar', id_user=id_user))

        updatesql(
            "usuario",
            "id_user",
            id_user,
            {
                "name_user": nombre,
                "apell_user": apellp,
                "apellm_user": apellm,
                "mail_user": email,
                "contra_user": contrasena,
                "edad_user": edad
            }
        )

        flash("Usuario actualizado correctamente", "success")
        return redirect(url_for('editar', id_user=id_user))

    return render_template("editar.html", id_user=id_user, usuario=usuario)

@app.route('/eliminar/<int:id_user>', methods=["GET", "POST"])
def eliminar(id_user): 
    usuario = busqueda("usuario", "id_user", id_user)
    usuario = usuario[0] if usuario else None

    if request.method == "POST":

        eliminar = deletesql("usuario", "id_user", id_user)
        if eliminar:
            flash("Usuario eliminado correctamente", "success")
            return redirect(url_for('tabla'))
        else:
            flash("Ha ocurrido un error inesperado")
            return redirect(url_for('eliminar', id_user=id_user))


    return render_template("eliminar.html", id_user=id_user, usuario=usuario)


if __name__ == "__main__":
    app.run(debug=True)