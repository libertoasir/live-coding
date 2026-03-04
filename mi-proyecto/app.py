import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "hackathon_key_2026"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

DATABASE = "database.db"

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, user_id INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    conn.commit()
    conn.close()
    print("✅ Tablas creadas correctamente.")

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return User(user[0], user[1]) if user else None

@app.route("/")
def index():
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form.get("username")
        pw = generate_password_hash(request.form.get("password"))
        try:
            conn = sqlite3.connect(DATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (user, pw))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except:
            return "El usuario ya existe", 400
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_in = request.form.get("username")
        pass_in = request.form.get("password")
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (user_in,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], pass_in):
            login_user(User(user[0], user[1]))
            return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            # Guardamos la nota
            c.execute("INSERT INTO notes (content, user_id) VALUES (?, ?)", (content, current_user.id))
            conn.commit()

    # ESTA LÍNEA ES LA CLAVE: Pedimos el ID, luego el Contenido y luego la Fecha
    c.execute("SELECT id, content, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC", (current_user.id,))
    notes = c.fetchall()
    
    conn.close()
    return render_template("dashboard.html", notes=notes)
@app.route("/delete-note/<int:note_id>")
@login_required
def delete_note(note_id):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    # Borramos la nota que coincida con el ID y que sea del usuario logueado
    c.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, current_user.id))
    conn.commit()
    conn.close()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))
@app.after_request
def add_header(response):
    # Dice al navegador que no guarde nada en caché
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)