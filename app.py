from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import datetime
import requests
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'Obreiros'

# Configuração do banco de dados
DATABASE = 'checkin.db'

def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = get_db_connection()
    
    # Tabela de membros (ALTERADA: grupo_celular → departamento)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS membros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            telefone TEXT,
            data_nascimento TEXT,
            departamento TEXT,  -- ALTERADO: grupo_celular → departamento
            lider_id INTEGER,
            FOREIGN KEY (lider_id) REFERENCES usuarios (id)
        )
    ''')
    
    # Tabela de check-ins
    conn.execute('''
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            membro_id INTEGER NOT NULL,
            data_checkin TEXT NOT NULL,
            tipo TEXT NOT NULL,
            localizacao TEXT,
            endereco_ip TEXT,
            user_agent TEXT,
            FOREIGN KEY (membro_id) REFERENCES membros (id)
        )
    ''')
    
    # Tabela de usuários (líderes)
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def criar_usuario_lider():
    """Cria um usuário líder padrão se não existir"""
    conn = get_db_connection()
    usuario_existe = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
    
    if usuario_existe == 0:
        password_hash = generate_password_hash('admin123')
        conn.execute(
            'INSERT INTO usuarios (username, password_hash, nome, email) VALUES (?, ?, ?, ?)',
            ('admin', password_hash, 'Administrador', 'admin@igreja.com')
        )
        conn.commit()
        print("✅ Usuário admin criado: username='admin', senha='admin123'")
    conn.close()

def criar_templates():
    """Cria os templates HTML necessários"""
    templates = {
        'base.html': '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sistema de Check-in - ADFidelidade{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="bi bi-house-door-fill"></i> ADFidelidade
            </a>
            <div class="navbar-nav ms-auto">
                {% if session.username %}
                <span class="navbar-text me-3">Olá, {{ session.nome }}</span>
                <a class="btn btn-outline-light btn-sm me-2" href="/">
                    <i class="bi bi-house"></i> Início
                </a>
                <a class="btn btn-outline-light btn-sm" href="/logout">
                    <i class="bi bi-box-arrow-right"></i> Sair
                </a>
                {% else %}
                <a class="btn btn-outline-light btn-sm" href="/login_lider">
                    <i class="bi bi-person-circle"></i> Área do Líder
                </a>
                {% endif %}
            </div>
        </div>
    </nav>

    <div class="container mt-4 min-vh-100">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ 'danger' if category == 'error' else 'success' }} alert-dismissible fade show">
                        {{ message }}
                        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        {% block content %}{% endblock %}
    </div>

    <footer class="bg-dark text-light mt-5 py-4">
        <div class="container">
            <div class="row">
                <div class="col-md-6">
                    <h5><i class="bi bi-geo-alt-fill"></i> ADFidelidade</h5>
                    <p>Sistema de Check-in de Obreiros</p>
                </div>
                <div class="col-md-6 text-end">
                    <p class="mb-0">&copy; 2024. Todos os direitos reservados.</p>
                </div>
            </div>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
''',
        'index.html': '''
{% extends "base.html" %}

{% block title %}Início - Sistema de Check-in{% endblock %}

{% block content %}
<div class="row">
    <div class="col-md-8 mx-auto text-center">
        <div class="hero-section mb-5">
            <h1 class="display-4 text-primary mb-3">
                <i class="bi bi-people-fill"></i> Sistema de Check-in
            </h1>
            <p class="lead">Bem-vindo ao sistema de check-in ADFidelidade</p>
        </div>

        <div class="row">
            <div class="col-md-6 mb-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h3 class="card-title text-primary">
                            <i class="bi bi-lightning-charge"></i> Check-in Rápido
                        </h3>
                        <p class="card-text">Faça seu check-in de forma rápida</p>
                        <a href="/checkin_rapido" class="btn btn-primary btn-lg">
                            Fazer Check-in
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6 mb-4">
                <div class="card h-100">
                    <div class="card-body">
                        <h3 class="card-title text-success">
                            <i class="bi bi-person-plus"></i> Cadastro
                        </h3>
                        <p class="card-text">Cadastre-se como Obreiro</p>
                        <a href="/cadastrar" class="btn btn-success btn-lg">
                            Cadastrar
                        </a>
                    </div>
                </div>
            </div>
        </div>

        <div class="mt-5">
            <div class="card">
                <div class="card-body">
                    <h4 class="card-title">
                        <i class="bi bi-info-circle"></i> Informações
                    </h4>
                    <p>Este sistema foi desenvolvido para facilitar o controle de presença dos Obreiros ADFidelidade.</p>
                    <p>Para acessar a área de líderes, faça login com suas credenciais.</p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',
        'login_lider.html': '''
{% extends "base.html" %}

{% block title %}Login - Área do Líder{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">
                    <i class="bi bi-person-circle"></i> Área do Líder - Login
                </h4>
            </div>
           
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="username" class="form-label">Usuário</label>
                        <input type="text" class="form-control" id="username" name="username" required>
                    </div>
                    <div class="mb-3">
                        <label for="password" class="form-label">Senha</label>
                        <input type="password" class="form-control" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="bi bi-box-arrow-in-right"></i> Entrar
                    </button>
                </form>
                
                <div class="mt-3 text-center">
                    <a href=" " class="btn btn-outline-secondary">
                        <i class="bi bi-arrow-left"></i> Voltar para o Início
                    </a>
                </div>
                
                <div class="mt-3">
                    <p class="text-muted">
                        <small>Credenciais padrão: admin / admin123</small>
                    </p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',
        'cadastrar.html': '''
{% extends "base.html" %}

{% block title %}Cadastro de Membro{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-8">
        <div class="card">
            <div class="card-header bg-success text-white">
                <h4 class="mb-0">
                    <i class="bi bi-person-plus"></i> Cadastro de Obreiros
                </h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="nome" class="form-label">Nome Completo *</label>
                            <input type="text" class="form-control" id="nome" name="nome" required>
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="email" class="form-label">Email *</label>
                            <input type="email" class="form-control" id="email" name="email" required>
                        </div>
                    </div>
                    
                    <div class="row">
                        <div class="col-md-6 mb-3">
                            <label for="telefone" class="form-label">Telefone</label>
                            <input type="tel" class="form-control" id="telefone" name="telefone">
                        </div>
                        <div class="col-md-6 mb-3">
                            <label for="data_nascimento" class="form-label">Data de Nascimento</label>
                            <input type="date" class="form-control" id="data_nascimento" name="data_nascimento">
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label for="departamento" class="form-label">Departamento</label>
                        <input type="text" class="form-control" id="departamento" name="departamento">
                    </div>
                    
                    <button type="submit" class="btn btn-success w-100">
                        <i class="bi bi-check-circle"></i> Cadastrar
                    </button>
                </form>
                
                <div class="mt-3 text-center">
                    <a href="/" class="btn btn-outline-secondary">
                        <i class="bi bi-arrow-left"></i> Voltar para o Início
                    </a>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',
        'checkin_rapido.html': '''
{% extends "base.html" %}

{% block title %}Check-in Rápido{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card">
            <div class="card-header bg-primary text-white">
                <h4 class="mb-0">
                    <i class="bi bi-lightning-charge"></i> Check-in Rápido
                </h4>
            </div>
            <div class="card-body">
                <form method="POST">
                    <div class="mb-3">
                        <label for="email" class="form-label">Email *</label>
                        <input type="email" class="form-control" id="email" name="email" 
                               placeholder="Digite o email cadastrado" required>
                    </div>
                    
                    <button type="submit" class="btn btn-primary w-100 mb-3">
                        <i class="bi bi-check-circle"></i> Fazer Check-in
                    </button>
                    
                    <div class="text-center">
                        <a href="/" class="btn btn-outline-secondary me-2">
                            <i class="bi bi-arrow-left"></i> Voltar
                        </a>
                        <a href="/cadastrar" class="btn btn-outline-success">
                            <i class="bi bi-person-plus"></i> Não tenho cadastro
                        </a>
                    </div>
                </form>
                
                <div class="mt-4">
                    <div class="alert alert-info">
                        <h6></i> Como funciona:</h6>
                        <p class="mb-0">Digite o email utilizado no cadastro para registrar sua presença.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
''',
        'painel_lider.html': '''
{% extends "base.html" %}

{% block title %}Painel do Líder{% endblock %}

{% block content %}
<div class="row mb-4">
    <div class="col-12">
        <div class="d-flex justify-content-between align-items-center">
            <h2 class="mb-0">
                <i class="bi bi-speedometer2"></i> Painel do Líder
            </h2>
            <div>
                <a href="/" class="btn btn-outline-primary btn-sm me-2">
                    <i class="bi bi-house"></i> Início
                </a>
                <a href="/logout" class="btn btn-outline-danger btn-sm">
                    <i class="bi bi-box-arrow-right"></极速赛车开奖直播i> Sair
                </a>
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <div class="col-md-4 mb-3">
        <div class="card text-white bg-primary">
            <div class="card-body">
                <h5 class="card-title">
                    <i class="bi bi-people-fill"></i> Total de Obreiros
                </h5>
                <h3 class="card-text">{{ total_membros }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-4 mb-3">
        <div class="card text-white bg-success">
            <div class="card-body">
                <h5 class="card-title">
                    <i class="bi bi-check-circle-fill"></i> Check-ins (7 dias)
                </h5>
                <h3 class="card-text">{{ checkins_recentes }}</h3>
            </div>
        </div>
    </div>
    <div class="col-md-4 mb-3">
        <div class="card text-white bg-info">
            <div class="card-body">
                <h5 class="card-title">
                    <i class="bi bi-person-check-fill"></i> Líder Logado
                </h5>
                <h6 class="card-text">{{ session.nome }}</h6>
            </div>
        </div>
    </div>
</div>

<div class="row mb-4">
    <div class="col-12">
        <div class="card">
            <div class="card-header bg-secondary text-white">
                <h5 class="mb-0">
                    <i class="bi bi-clock-history"></i> Últimos Check-ins
                </h5>
            </div>
            <div class="card-body">
                {% if ultimos_checkins %}
                <div class="table-responsive">
                    <table class="table table-striped">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>Data/Hora</th>
                                <th>Tipo</th>
                                <th>Localização</th>  <!-- NOVO: Coluna de localização -->
                            </tr>
                        </thead>
                        <tbody>
                            {% for checkin in ultimos_checkins %}
                            <tr>
                                <td>{{ checkin['nome'] }}</td>
                                <td>{{ checkin['data_checkin'] }}</td>
                                <td>{{ checkin['tipo'] }}</td>
                                <td>{{ checkin['localizacao'] or 'N/A' }}</td>  <!-- NOVO: Mostrar localização -->
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p class="text-muted">Nenhum check-in registrado ainda.</p>
                {% endif %}
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-12">
        <div class="card">
            <div class="card-header bg-dark text-white">
                <h5 class="mb-0">
                    <i class="bi bi-list-ul"></i> Lista de Obreiros
                </h5>
            </div>
            <div class="card-body">
                {% if membros %}
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th>Nome</th>
                                <th>Email</th>
                                <th>Telefone</th>
                                <th>Departamento</th>  <!-- ALTERADO: grupo_celular → departamento -->
                            </tr>
                        </thead>
                        <tbody>
                            {% for membro in membros %}
                            <tr>
                                <td>{{ membro['nome'] }}</td>
                                <td>{{ membro['email'] }}</td>
                                <td>{{ membro['telefone'] or 'N/A' }}</td>
                                <td>{{ membro['departamento'] or 'N/A' }}</td>  <!-- ALTERADO: grupo_celular → departamento -->
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% else %}
                <p class="text-muted">Nenhum obreiro cadastrado ainda.</p>
                {% endif %}
            </div>
        </div>
    </div>
</div>
{% endblock %}
'''
    }
    
    # Criar pasta templates se não existir
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Criar arquivos de template
    for filename, content in templates.items():
        filepath = os.path.join('templates', filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Template {filename} criado")

# Rotas da aplicação
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login_lider', methods=['GET', 'POST'])
def login_lider():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE username = ?', (username,)
        ).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nome'] = user['nome']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('painel_lider'))
        else:
            flash('Usuário ou senha incorretos', 'error')
    
    return render_template('login_lider.html')

@app.route('/painel_lider')
def painel_lider():
    if 'user_id' not in session:
        return redirect(url_for('login_lider'))
    
    conn = get_db_connection()
    
    total_membros = conn.execute('SELECT COUNT(*) FROM membros').fetchone()[0]
    
    sete_dias_atras = (datetime.datetime.now() - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    checkins_recentes = conn.execute(
        'SELECT COUNT(*) FROM checkins WHERE data_checkin >= ?', 
        (sete_dias_atras,)
    ).fetchone()[0]
    
    # ALTERADO: Incluir localização na consulta
    ultimos_checkins = conn.execute('''
        SELECT m.nome, c.data_checkin, c.tipo, c.localizacao 
        FROM checkins c
        JOIN membros m ON c.membro_id = m.id
        ORDER BY c.data_checkin DESC
        LIMIT 10
    ''').fetchall()
    
    membros = conn.execute('SELECT * FROM membros ORDER BY nome').fetchall()
    
    conn.close()
    
    return render_template('painel_lider.html',
                         total_membros=total_membros,
                         checkins_recentes=checkins_recentes,
                         ultimos_checkins=ultimos_checkins,
                         membros=membros)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefone = request.form.get('telefone', '')
        data_nascimento = request.form.get('data_nascimento', '')
        departamento = request.form.get('departamento', '')  # ALTERADO: grupo_celular → departamento
        
        conn = get_db_connection()
        try:
            # ALTERADO: grupo_celular → departamento
            conn.execute(
                'INSERT INTO membros (nome, email, telefone, data_nascimento, departamento) VALUES (?, ?, ?, ?, ?)',
                (nome, email, telefone, data_nascimento, departamento)
            )
            conn.commit()
            flash('Obreiro cadastrado com sucesso!', 'success')
        except sqlite3.IntegrityError:
            flash('Email já cadastrado', 'error')
        finally:
            conn.close()
        
        return redirect(url_for('cadastrar'))
    
    return render_template('cadastrar.html')

@app.route('/checkin_rapido', methods=['GET', 'POST'])
def checkin_rapido():
    if request.method == 'POST':
        email = request.form['email']
        
        conn = get_db_connection()
        membro = conn.execute(
            'SELECT * FROM membros WHERE email = ?', (email,)
        ).fetchone()
        
        if membro:
            try:
                response = requests.get('https://ipapi.co/json/', timeout=5)
                localizacao_data = response.json()
                localizacao = f"{localizacao_data.get('city', 'N/A')}, {localizacao_data.get('region', 'N/A')}, {localizacao_data.get('country_name', 'N/A')}"
                endereco_ip = localizacao_data.get('ip', 'N/A')
            except Exception as e:
                print(f"Erro ao obter localização: {e}")
                localizacao = "Localização não disponível"
                endereco_ip = "N/A"
            
            data_atual = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            user_agent = request.headers.get('User-Agent', 'N/A')
            
            conn.execute(
                'INSERT INTO checkins (membro_id, data_checkin, tipo, localizacao, endereco_ip, user_agent) VALUES (?, ?, ?, ?, ?, ?)',
                (membro['id'], data_atual, 'rápido', localizacao, endereco_ip, user_agent)
            )
            conn.commit()
            conn.close()
            
            flash(f'Check-in realizado para {membro["nome"]}! Localização: {localizacao}', 'success')
        else:
            conn.close()
            flash('Email não encontrado. Por favor, faça o cadastro primeiro.', 'error')
        
        return redirect(url_for('checkin_rapido'))
    
    return render_template('checkin_rapido.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('index'))

# Inicialização
if __name__ == '__main__':
    print("🚀 Inicializando sistema...")
    init_db()
    criar_usuario_lider()
    criar_templates()
    print("✅ Sistema pronto! Acesse http://localhost:5000")
    print("🔐 Credenciais: usuário 'admin', senha 'admin123'")
    app.run(debug=True, port=5000)