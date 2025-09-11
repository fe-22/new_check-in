import os
import datetime
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import create_engine, text

# Configuração Flask
app = Flask(__name__, template_folder="../templates")
app.secret_key = 'obreiros'

# ------------------ Configuração do Banco (PostgreSQL via Render) ------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não encontrada nas variáveis de ambiente")

# Render às vezes retorna postgres:// em vez de postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# Criar engine global
engine = create_engine(DATABASE_URL, future=True)

# ------------------ Funções auxiliares ------------------
def init_db():
    """Cria as tabelas necessárias no Postgres."""
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            criado TIMESTAMP DEFAULT NOW()
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS membros (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            grupo TEXT,
            presente BOOLEAN DEFAULT FALSE,
            data_checkin TIMESTAMP
        );
        """))

# ------------------ Rotas ------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    nome = request.form["nome"]
    email = request.form["email"]
    senha = generate_password_hash(request.form["senha"])

    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO usuarios (nome, email, senha) VALUES (:n, :e, :s)"),
                         {"n": nome, "e": email, "s": senha})
        flash("Usuário registrado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao registrar usuário: {e}", "danger")
    return redirect(url_for("index"))

@app.route("/login", methods=["POST"])
def login():
    email = request.form["email"]
    senha = request.form["senha"]

    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM usuarios WHERE email = :e"), {"e": email}).fetchone()

    if result and check_password_hash(result.senha, senha):
        session["usuario_id"] = result.id
        session["usuario_nome"] = result.nome
        flash("Login bem-sucedido!", "success")
        return redirect(url_for("painel_lider"))
    else:
        flash("Credenciais inválidas", "danger")
        return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso.", "info")
    return redirect(url_for("index"))

@app.route("/painel_lider")
def painel_lider():
    if "usuario_id" not in session:
        flash("Faça login primeiro.", "warning")
        return redirect(url_for("index"))

    with engine.connect() as conn:
        membros = conn.execute(text("SELECT * FROM membros ORDER BY nome")).fetchall()

    return render_template("painel_lider.html", membros=membros)

@app.route("/checkin", methods=["POST"])
def checkin():
    membro_id = request.form["membro_id"]
    presente = request.form.get("presente") == "on"

    with engine.begin() as conn:
        conn.execute(text("UPDATE membros SET presente = :p, data_checkin = :d WHERE id = :id"),
                     {"p": presente, "d": datetime.datetime.now(), "id": membro_id})
    flash("Check-in atualizado com sucesso!", "success")
    return redirect(url_for("painel_lider"))

# ------------------ Inicialização ------------------
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
