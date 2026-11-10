"""Sistema de Gestión de Tareas - Plásticos Sustentables.

Flask + SQLite. Funcionalidades: registro/login, CRUD de tareas, asignación,
filtrado y búsqueda, tareas completadas/pendientes y gestión de perfil.
"""
import os
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from validators import (ESTADOS, PRIORIDADES, validar_email, validar_password,
                        validar_tarea)

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo TEXT NOT NULL,
    descripcion TEXT DEFAULT '',
    prioridad TEXT NOT NULL DEFAULT 'media',
    fecha_limite TEXT,
    estado TEXT NOT NULL DEFAULT 'pendiente',
    creador_id INTEGER NOT NULL REFERENCES usuarios(id),
    asignado_id INTEGER NOT NULL REFERENCES usuarios(id)
);
"""


def create_app(config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get("SECRET_KEY", "cambiar-en-produccion"),
        DATABASE=os.path.join(app.instance_path, "tareas.db"),
    )
    if config:
        app.config.update(config)
    os.makedirs(app.instance_path, exist_ok=True)

    # ---------- Base de datos ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        get_db().executescript(SCHEMA)

    # ---------- Autenticación ----------
    @app.before_request
    def cargar_usuario():
        uid = session.get("user_id")
        g.user = None
        if uid:
            g.user = get_db().execute(
                "SELECT * FROM usuarios WHERE id = ?", (uid,)).fetchone()

    def login_required(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("login"))
            return vista(*args, **kwargs)
        return envoltura

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            error = None
            if not nombre:
                error = "El nombre es obligatorio."
            elif not validar_email(email):
                error = "El correo no es válido."
            elif not validar_password(password):
                error = ("La contraseña debe tener mínimo 8 caracteres, "
                         "con letras y números.")
            if error is None:
                try:
                    get_db().execute(
                        "INSERT INTO usuarios (nombre, email, password_hash) "
                        "VALUES (?, ?, ?)",
                        (nombre, email, generate_password_hash(password)))
                    get_db().commit()
                    flash("Cuenta creada. Ya puedes iniciar sesión.", "ok")
                    return redirect(url_for("login"))
                except sqlite3.IntegrityError:
                    error = "Ese correo ya está registrado."
            flash(error, "error")
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("tareas"))
            flash("Correo o contraseña incorrectos.", "error")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---------- Tareas ----------
    def obtener_tarea(tarea_id):
        """Devuelve la tarea solo si el usuario es el creador o el asignado."""
        t = get_db().execute(
            "SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
        if t is None:
            abort(404)
        if g.user["id"] not in (t["creador_id"], t["asignado_id"]):
            abort(403)
        return t

    def usuarios_disponibles():
        return get_db().execute(
            "SELECT id, nombre FROM usuarios ORDER BY nombre").fetchall()

    @app.route("/")
    @login_required
    def tareas():
        q = request.args.get("q", "").strip()
        estado = request.args.get("estado", "")
        prioridad = request.args.get("prioridad", "")
        sql = ("SELECT t.*, u.nombre AS asignado_nombre FROM tareas t "
               "JOIN usuarios u ON u.id = t.asignado_id "
               "WHERE (t.creador_id = ? OR t.asignado_id = ?)")
        params = [g.user["id"], g.user["id"]]
        if q:
            sql += " AND (t.titulo LIKE ? OR t.descripcion LIKE ?)"
            params += [f"%{q}%", f"%{q}%"]
        if estado in ESTADOS:
            sql += " AND t.estado = ?"
            params.append(estado)
        if prioridad in PRIORIDADES:
            sql += " AND t.prioridad = ?"
            params.append(prioridad)
        sql += " ORDER BY t.estado DESC, t.fecha_limite IS NULL, t.fecha_limite"
        lista = get_db().execute(sql, params).fetchall()
        return render_template("tareas.html", tareas=lista, q=q,
                               estado=estado, prioridad=prioridad,
                               prioridades=PRIORIDADES, estados=ESTADOS)

    def _guardar_tarea(tarea=None):
        titulo = request.form.get("titulo", "")
        descripcion = request.form.get("descripcion", "").strip()
        prioridad = request.form.get("prioridad", "media")
        fecha = request.form.get("fecha_limite", "").strip() or None
        asignado = request.form.get("asignado_id", type=int) or g.user["id"]
        errores = validar_tarea(titulo, prioridad, fecha)
        existe = get_db().execute(
            "SELECT 1 FROM usuarios WHERE id = ?", (asignado,)).fetchone()
        if not existe:
            errores.append("El usuario asignado no existe.")
        if errores:
            for e in errores:
                flash(e, "error")
            return False
        db = get_db()
        if tarea is None:
            db.execute(
                "INSERT INTO tareas (titulo, descripcion, prioridad, "
                "fecha_limite, creador_id, asignado_id) VALUES (?,?,?,?,?,?)",
                (titulo.strip(), descripcion, prioridad, fecha,
                 g.user["id"], asignado))
        else:
            db.execute(
                "UPDATE tareas SET titulo=?, descripcion=?, prioridad=?, "
                "fecha_limite=?, asignado_id=? WHERE id=?",
                (titulo.strip(), descripcion, prioridad, fecha, asignado,
                 tarea["id"]))
        db.commit()
        return True

    @app.route("/tareas/nueva", methods=["GET", "POST"])
    @login_required
    def tarea_nueva():
        if request.method == "POST" and _guardar_tarea():
            flash("Tarea creada.", "ok")
            return redirect(url_for("tareas"))
        return render_template("tarea_form.html", tarea=None,
                               usuarios=usuarios_disponibles(),
                               prioridades=PRIORIDADES)

    @app.route("/tareas/<int:tarea_id>/editar", methods=["GET", "POST"])
    @login_required
    def tarea_editar(tarea_id):
        tarea = obtener_tarea(tarea_id)
        if tarea["creador_id"] != g.user["id"]:
            abort(403)  # solo quien creó la tarea puede editarla
        if request.method == "POST" and _guardar_tarea(tarea):
            flash("Tarea actualizada.", "ok")
            return redirect(url_for("tareas"))
        return render_template("tarea_form.html", tarea=tarea,
                               usuarios=usuarios_disponibles(),
                               prioridades=PRIORIDADES)

    @app.route("/tareas/<int:tarea_id>/eliminar", methods=["POST"])
    @login_required
    def tarea_eliminar(tarea_id):
        tarea = obtener_tarea(tarea_id)
        if tarea["creador_id"] != g.user["id"]:
            abort(403)
        get_db().execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        get_db().commit()
        flash("Tarea eliminada.", "ok")
        return redirect(url_for("tareas"))

    @app.route("/tareas/<int:tarea_id>/estado", methods=["POST"])
    @login_required
    def tarea_estado(tarea_id):
        tarea = obtener_tarea(tarea_id)
        nuevo = "pendiente" if tarea["estado"] == "completada" else "completada"
        get_db().execute("UPDATE tareas SET estado=? WHERE id=?",
                         (nuevo, tarea_id))
        get_db().commit()
        return redirect(url_for("tareas"))

    # ---------- Perfil ----------
    @app.route("/perfil", methods=["GET", "POST"])
    @login_required
    def perfil():
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            email = request.form.get("email", "").strip().lower()
            if not nombre:
                flash("El nombre es obligatorio.", "error")
            elif not validar_email(email):
                flash("El correo no es válido.", "error")
            else:
                try:
                    get_db().execute(
                        "UPDATE usuarios SET nombre=?, email=? WHERE id=?",
                        (nombre, email, g.user["id"]))
                    get_db().commit()
                    flash("Perfil actualizado.", "ok")
                    return redirect(url_for("perfil"))
                except sqlite3.IntegrityError:
                    flash("Ese correo ya está en uso.", "error")
        return render_template("perfil.html")

    @app.route("/perfil/password", methods=["POST"])
    @login_required
    def cambiar_password():
        actual = request.form.get("actual", "")
        nueva = request.form.get("nueva", "")
        if not check_password_hash(g.user["password_hash"], actual):
            flash("La contraseña actual es incorrecta.", "error")
        elif not validar_password(nueva):
            flash("La nueva contraseña debe tener mínimo 8 caracteres, "
                  "con letras y números.", "error")
        else:
            get_db().execute(
                "UPDATE usuarios SET password_hash=? WHERE id=?",
                (generate_password_hash(nueva), g.user["id"]))
            get_db().commit()
            flash("Contraseña actualizada.", "ok")
        return redirect(url_for("perfil"))

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
