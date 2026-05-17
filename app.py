from flask import Flask, render_template, request, redirect, url_for, jsonify, session, make_response, g, flash
import sqlite3
import os
from datetime import datetime
import json
import csv
import io
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-12345')
DATABASE = os.environ.get('DATABASE', 'clinica_v1.db')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON;')
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        db.executescript('''
            CREATE TABLE IF NOT EXISTS terapeutas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                especialidade TEXT NOT NULL,
                registro_profissional TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS aprendizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                data_nascimento TEXT NOT NULL,
                cpf TEXT NOT NULL,
                cid TEXT,
                nome_responsavel TEXT NOT NULL,
                telefone_responsavel TEXT NOT NULL,
                email_responsavel TEXT NOT NULL,
                status TEXT DEFAULT 'Avaliação',
                terapeuta_id INTEGER,
                foto_url TEXT,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (terapeuta_id) REFERENCES terapeutas (id)
            );
            CREATE TABLE IF NOT EXISTS checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aprendiz_id INTEGER NOT NULL,
                terapeuta_id INTEGER NOT NULL,
                data_inicio TEXT NOT NULL,
                data_termino TEXT,
                respostas TEXT NOT NULL,
                status TEXT DEFAULT 'Incompleto',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aprendiz_id) REFERENCES aprendizes (id),
                FOREIGN KEY (terapeuta_id) REFERENCES terapeutas (id)
            );
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                nome TEXT NOT NULL,
                cargo TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        db.commit()
        
        cursor = db.cursor()
        
        cursor.execute('SELECT count(*) FROM usuarios WHERE username = ?', ('root',))
        if cursor.fetchone()[0] == 0:
            hashed_pw = generate_password_hash('root123!')
            db.execute('INSERT INTO usuarios (username, password_hash, nome, cargo) VALUES (?, ?, ?, ?)',
                       ('root', hashed_pw, 'João Paulo', 'Administrador'))
            db.commit()

init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('painel'))
    
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        db = get_db()
        user = db.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['nome'] = user['nome']
            session['cargo'] = user['cargo']
            return redirect(url_for('painel'))
        else:
            error = 'Usuário ou senha inválidos.'
            
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

def fetch_aprendizes(db, filters):
    query = '''
        SELECT a.*, t.nome as nome_terapeuta,
        strftime('%d/%m/%Y', a.criado_em) as data_formatada
        FROM aprendizes a 
        LEFT JOIN terapeutas t ON a.terapeuta_id = t.id 
        WHERE 1=1
    '''
    params = []
    
    if filters.get('nome'):
        query += " AND a.nome LIKE ?"
        params.append(f"%{filters.get('nome')}%")
    if filters.get('responsavel'):
        query += " AND a.nome_responsavel LIKE ?"
        params.append(f"%{filters.get('responsavel')}%")
    if filters.get('terapeuta'):
        query += " AND t.nome LIKE ?"
        params.append(f"%{filters.get('terapeuta')}%")
    if filters.get('status'):
        query += " AND a.status = ?"
        params.append(filters.get('status'))
        
    query += " ORDER BY a.criado_em DESC"
    return db.execute(query, params).fetchall()

@app.route('/')
@login_required
def painel():
    db = get_db()
    
    ap_filters = {
        'nome': request.args.get('ap_nome'),
        'responsavel': request.args.get('ap_responsavel'),
        'terapeuta': request.args.get('ap_terapeuta'),
        'status': request.args.get('ap_status')
    }
    aprendizes = fetch_aprendizes(db, ap_filters)

    ck_query = '''
        SELECT c.*, a.nome as nome_aprendiz, t.nome as nome_terapeuta,
        strftime('%d/%m/%Y', c.criado_em) as data_formatada
        FROM checklists c 
        JOIN aprendizes a ON c.aprendiz_id = a.id 
        JOIN terapeutas t ON c.terapeuta_id = t.id 
        WHERE 1=1
    '''
    ck_params = []
    if request.args.get('ck_aprendiz'):
        ck_query += " AND a.nome LIKE ?"
        ck_params.append(f"%{request.args.get('ck_aprendiz')}%")
    if request.args.get('ck_terapeuta'):
        ck_query += " AND t.nome LIKE ?"
        ck_params.append(f"%{request.args.get('ck_terapeuta')}%")
    if request.args.get('ck_status'):
        ck_query += " AND c.status = ?"
        ck_params.append(request.args.get('ck_status'))
    ck_query += " ORDER BY c.criado_em DESC"
    
    checklists = db.execute(ck_query, ck_params).fetchall()
    return render_template('painel.html', aprendizes=aprendizes, checklists=checklists)

@app.route('/aprendizes')
@login_required
def lista_aprendizes():
    db = get_db()
    
    filters = {
        'nome': request.args.get('nome'),
        'responsavel': request.args.get('responsavel'),
        'terapeuta': request.args.get('terapeuta'),
        'status': request.args.get('status')
    }
    aprendizes = fetch_aprendizes(db, filters)
    
    return render_template('lista_aprendizes.html', aprendizes=aprendizes)

@app.route('/terapeutas')
@login_required
def lista_terapeutas():
    if session.get('cargo') != 'Administrador':
        return redirect(url_for('painel'))
    db = get_db()
    
    query = "SELECT *, strftime('%d/%m/%Y', criado_em) as data_formatada FROM terapeutas WHERE 1=1"
    params = []
    
    filter_nome = request.args.get('nome')
    if filter_nome:
        query += " AND nome LIKE ?"
        params.append(f"%{filter_nome}%")
        
    filter_especialidade = request.args.get('especialidade')
    if filter_especialidade:
        query += " AND especialidade LIKE ?"
        params.append(f"%{filter_especialidade}%")
        
    filter_registro = request.args.get('registro')
    if filter_registro:
        query += " AND registro_profissional LIKE ?"
        params.append(f"%{filter_registro}%")
        
    query += " ORDER BY criado_em DESC"
    
    terapeutas = db.execute(query, params).fetchall()
    return render_template('terapeutas.html', terapeutas=terapeutas)


import math

@app.route('/importar-aprendizes', methods=['POST'])
@login_required
def importar_aprendizes():
    db = get_db()
    
    if 'file' not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(request.referrer)
        
    file = request.files['file']
    if not file or not file.filename.endswith('.csv'):
        flash("Por favor, envie um arquivo .csv.", "error")
        return redirect(request.referrer)
        
    stream = io.StringIO(file.stream.read().decode("UTF-8", errors='replace'), newline=None)
    csv_input = csv.DictReader(stream)
    
    expected_headers = ['Nome', 'Nascimento', 'CPF', 'CID', 'Responsável', 'Telefone', 'Email', 'Status', 'Terapeuta']
    if not csv_input.fieldnames or not all(h in csv_input.fieldnames for h in expected_headers):
        flash("O schema do CSV de aprendizes é inválido.", "error")
        return redirect(request.referrer)
    
    count = 0
    for row in csv_input:
        terapeuta = db.execute('SELECT id FROM terapeutas WHERE nome = ?', (row.get('Terapeuta'),)).fetchone()
        terapeuta_id = terapeuta['id'] if terapeuta else None
        
        db.execute('''
            INSERT INTO aprendizes (nome, data_nascimento, cpf, cid, nome_responsavel, telefone_responsavel, email_responsavel, status, terapeuta_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            row.get('Nome', ''), row.get('Nascimento', ''), row.get('CPF', ''), row.get('CID', ''),
            row.get('Responsável', ''), row.get('Telefone', ''), row.get('Email', ''), row.get('Status', 'Avaliação'),
            terapeuta_id
        ))
        count += 1
    db.commit()
    flash(f"{count} aprendizes importados com sucesso!", "success")
    return redirect(request.referrer)

@app.route('/importar-terapeutas', methods=['POST'])
@login_required
def importar_terapeutas():
    if session.get('cargo') != 'Administrador':
        return redirect(request.referrer)
        
    db = get_db()
    if 'file' not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(request.referrer)
        
    file = request.files['file']
    if not file or not file.filename.endswith('.csv'):
        flash("Por favor, envie um arquivo .csv.", "error")
        return redirect(request.referrer)
        
    stream = io.StringIO(file.stream.read().decode("UTF-8", errors='replace'), newline=None)
    csv_input = csv.DictReader(stream)
    
    expected_headers = ['Nome', 'Especialidade', 'Registro Profissional']
    if not csv_input.fieldnames or not all(h in csv_input.fieldnames for h in expected_headers):
        flash("O schema do CSV de terapeutas é inválido.", "error")
        return redirect(request.referrer)
    
    count = 0
    for row in csv_input:
        db.execute('''
            INSERT INTO terapeutas (nome, especialidade, registro_profissional)
            VALUES (?, ?, ?)
        ''', (
            row.get('Nome', ''), row.get('Especialidade', ''), row.get('Registro Profissional', '')
        ))
        count += 1
    db.commit()
    flash(f"{count} terapeutas importados com sucesso!", "success")
    return redirect(request.referrer)

@app.route('/importar-checklists', methods=['POST'])
@login_required
def importar_checklists():
    db = get_db()
    if 'file' not in request.files:
        flash("Nenhum arquivo enviado.", "error")
        return redirect(request.referrer)
        
    file = request.files['file']
    if not file or not file.filename.endswith('.csv'):
        flash("Por favor, envie um arquivo .csv.", "error")
        return redirect(request.referrer)
        
    stream = io.StringIO(file.stream.read().decode("UTF-8", errors='replace'), newline=None)
    csv_input = csv.DictReader(stream)
    
    expected_headers = ['Aprendiz', 'Terapeuta', 'Data Inicio', 'Data Termino', 'Status']
    if not csv_input.fieldnames or not all(h in csv_input.fieldnames for h in expected_headers):
        flash("O schema do CSV de checklists é inválido.", "error")
        return redirect(request.referrer)
    
    count = 0
    for row in csv_input:
        aprendiz = db.execute('SELECT id FROM aprendizes WHERE nome = ?', (row.get('Aprendiz'),)).fetchone()
        terapeuta = db.execute('SELECT id FROM terapeutas WHERE nome = ?', (row.get('Terapeuta'),)).fetchone()
        
        if aprendiz and terapeuta:
            db.execute('''
                INSERT INTO checklists (aprendiz_id, terapeuta_id, data_inicio, data_termino, status, respostas)
                VALUES (?, ?, ?, ?, ?, '{}')
            ''', (
                aprendiz['id'], terapeuta['id'], row.get('Data Inicio', ''), row.get('Data Termino', ''), row.get('Status', 'Incompleto')
            ))
            count += 1
    db.commit()
    flash(f"{count} checklists importados com sucesso!", "success")
    return redirect(request.referrer)

def generate_csv_response(headers, rows, filename):
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(headers)
    for row in rows:
        cw.writerow(row)
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f"attachment; filename={filename}"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/exportar-aprendizes')
@login_required
def exportar_aprendizes():
    db = get_db()
    aprendizes = db.execute('''
        SELECT a.*, t.nome as nome_terapeuta
        FROM aprendizes a 
        LEFT JOIN terapeutas t ON a.terapeuta_id = t.id 
        ORDER BY a.criado_em DESC
    ''').fetchall()
    
    headers = ['Nome', 'Nascimento', 'CPF', 'CID', 'Responsável', 'Telefone', 'Email', 'Status', 'Terapeuta', 'Criado Em']
    rows = [
        [a['nome'], a['data_nascimento'], a['cpf'], a['cid'], a['nome_responsavel'], a['telefone_responsavel'], a['email_responsavel'], a['status'], a['nome_terapeuta'], a['criado_em']]
        for a in aprendizes
    ]
    return generate_csv_response(headers, rows, 'aprendizes.csv')

@app.route('/exportar-terapeutas')
@login_required
def exportar_terapeutas():
    if session.get('cargo') != 'Administrador':
        return redirect(url_for('painel'))
    db = get_db()
    terapeutas = db.execute('''
        SELECT * FROM terapeutas ORDER BY criado_em DESC
    ''').fetchall()
    
    headers = ['Nome', 'Especialidade', 'Registro Profissional', 'Criado Em']
    rows = [
        [t['nome'], t['especialidade'], t['registro_profissional'], t['criado_em']]
        for t in terapeutas
    ]
    return generate_csv_response(headers, rows, 'terapeutas.csv')

@app.route('/exportar-checklists')
@login_required
def exportar_checklists():
    db = get_db()
    checklists = db.execute('''
        SELECT c.*, a.nome as nome_aprendiz, t.nome as nome_terapeuta,
        strftime('%d/%m/%Y', c.criado_em) as data_formatada
        FROM checklists c 
        JOIN aprendizes a ON c.aprendiz_id = a.id 
        JOIN terapeutas t ON c.terapeuta_id = t.id 
        ORDER BY c.criado_em DESC
    ''').fetchall()
    
    headers = ['Aprendiz', 'Terapeuta', 'Data Inicio', 'Data Termino', 'Status', 'Criado Em']
    rows = [
        [c['nome_aprendiz'], c['nome_terapeuta'], c['data_inicio'], c['data_termino'], c['status'], c['criado_em']]
        for c in checklists
    ]
    return generate_csv_response(headers, rows, 'checklists.csv')

@app.route('/cadastro-terapeuta', methods=['GET', 'POST'])
@login_required
def cadastro_terapeuta():
    if session.get('cargo') != 'Administrador':
        return redirect(url_for('painel'))
    db = get_db()
    if request.method == 'POST':
        nome = request.form['nome']
        especialidade = request.form['especialidade']
        registro = request.form.get('registro_profissional', 'N/A')
        username = request.form['username']
        
        existing_user = db.execute('SELECT id FROM usuarios WHERE username = ?', (username,)).fetchone()
        if existing_user:
            return render_template('cadastro_terapeuta.html', error='Nome de usuário já está em uso.')
            
        password = request.form['password']
        cargo = request.form['cargo']
        hashed_pw = generate_password_hash(password)
        db.execute('INSERT INTO usuarios (username, password_hash, nome, cargo) VALUES (?, ?, ?, ?)',
                   (username, hashed_pw, nome, cargo))
        db.execute('INSERT INTO terapeutas (nome, especialidade, registro_profissional) VALUES (?, ?, ?)', 
                   (nome, especialidade, registro))
        db.commit()
        return redirect(url_for('lista_terapeutas'))
    return render_template('cadastro_terapeuta.html')

@app.route('/cadastro', methods=['GET', 'POST'])
@login_required
def cadastro():
    db = get_db()
    if request.method == 'POST':
        db.execute('''
            INSERT INTO aprendizes (nome, data_nascimento, cpf, cid, nome_responsavel, telefone_responsavel, email_responsavel, status, terapeuta_id, foto_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (request.form['nome'], request.form['data_nascimento'], request.form['cpf'], request.form.get('cid'), 
              request.form['nome_responsavel'], request.form['telefone_responsavel'], request.form['email_responsavel'], 
              request.form['status'], request.form['terapeuta_id'], request.form.get('foto_url')))
        db.commit()
        return redirect(url_for('painel'))
    terapeutas = db.execute('SELECT * FROM terapeutas').fetchall()
    return render_template('cadastro.html', terapeutas=terapeutas, aprendiz=None)

@app.route('/visualizar-aprendiz/<int:id>')
@login_required
def visualizar_aprendiz(id):
    db = get_db()
    aprendiz = db.execute('''
        SELECT a.*, t.nome as nome_terapeuta 
        FROM aprendizes a 
        LEFT JOIN terapeutas t ON a.terapeuta_id = t.id 
        WHERE a.id = ?
    ''', (id,)).fetchone()
    return render_template('visualizar_aprendiz.html', aprendiz=aprendiz)

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    db = get_db()
    if request.method == 'POST':
        db.execute('''
            UPDATE aprendizes SET nome=?, data_nascimento=?, cpf=?, cid=?, nome_responsavel=?, telefone_responsavel=?, email_responsavel=?, status=?, terapeuta_id=?, foto_url=?
            WHERE id=?
        ''', (request.form['nome'], request.form['data_nascimento'], request.form['cpf'], request.form.get('cid'), 
              request.form['nome_responsavel'], request.form['telefone_responsavel'], request.form['email_responsavel'], 
              request.form['status'], request.form['terapeuta_id'], request.form.get('foto_url'), id))
        db.commit()
        return redirect(url_for('painel'))
    aprendiz = db.execute('SELECT * FROM aprendizes WHERE id = ?', (id,)).fetchone()
    terapeutas = db.execute('SELECT * FROM terapeutas').fetchall()
    return render_template('cadastro.html', terapeutas=terapeutas, aprendiz=aprendiz)

@app.route('/excluir/<int:id>', methods=['POST'])
@login_required
def excluir(id):
    db = get_db()
    db.execute('DELETE FROM aprendizes WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('painel'))

@app.route('/selecao-aprendiz')
@login_required
def selecao_aprendiz():
    db = get_db()
    aprendizes = db.execute('SELECT * FROM aprendizes').fetchall()
    return render_template('selecao_aprendiz.html', aprendizes=aprendizes)

def get_habilidades():
    return [
        {'categoria': 'Habilidades de Atenção', 'itens': ['Sentar', 'Esperar', 'Contato Visual']},
        {'categoria': 'Habilidades de Imitação', 'itens': ['Imitar movimentos motores grossos', 'Imitar ações com objetos']},
        {'categoria': 'Habilidades de Ouvinte', 'itens': ['Seguir instruções de um passo', 'Identificar objetos', 'Identificar figuras', 'Identificar partes do corpo']},
        {'categoria': 'Habilidades Verbais', 'itens': ['Apontar para itens desejados', 'Produzir sons com função comunicativa', 'Pedir vocalmente por coisas', 'Nomear partes do corpo', 'Nomear objetos', 'Nomear figuras']},
        {'categoria': 'Habilidades de Percepção Visual e Emparelhamento com Modelo', 'itens': ['Coordenação olho mão', 'Emparelhar objetos', 'Emparelhar figuras']},
        {'categoria': 'Habilidades de Brincar', 'itens': ['Exploração de objetos', 'Dá função para o objeto']}
    ]

def process_checklist_form(form_data):
    respostas = {}
    itens_respondidos = 0
    for key in form_data:
        if key.startswith('resp_'):
            item = key.replace('resp_', '')
            respostas[item] = {
                'valor': form_data[key],
                'observacao': form_data.get(f'obs_{item}', '')
            }
            itens_respondidos += 1
    return respostas, itens_respondidos

@app.route('/checklist/<int:aprendiz_id>', methods=['GET', 'POST'])
@login_required
def checklist(aprendiz_id):
    db = get_db()
    habilidades = get_habilidades()
    total_itens = sum(len(cat['itens']) for cat in habilidades)
    
    if request.method == 'POST':
        respostas, itens_respondidos = process_checklist_form(request.form)
        status = 'Concluído' if itens_respondidos == total_itens else 'Incompleto'
        aprendiz = db.execute('SELECT * FROM aprendizes WHERE id = ?', (aprendiz_id,)).fetchone()
        
        db.execute('''
            INSERT INTO checklists (aprendiz_id, terapeuta_id, data_inicio, data_termino, respostas, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (aprendiz_id, aprendiz['terapeuta_id'], request.form['data_inicio'], request.form['data_termino'], json.dumps(respostas), status))
        db.commit()
        return redirect(url_for('painel'))
    
    aprendiz = db.execute('SELECT * FROM aprendizes WHERE id = ?', (aprendiz_id,)).fetchone()
    return render_template('checklist.html', aprendiz=aprendiz, habilidades=habilidades)

@app.route('/visualizar-checklist/<int:id>')
@login_required
def visualizar_checklist(id):
    db = get_db()
    checklist_row = db.execute('SELECT * FROM checklists WHERE id = ?', (id,)).fetchone()
    aprendiz = db.execute('SELECT * FROM aprendizes WHERE id = ?', (checklist_row['aprendiz_id'],)).fetchone()
    habilidades = get_habilidades()
    respostas = json.loads(checklist_row['respostas'])
    return render_template('checklist.html', aprendiz=aprendiz, habilidades=habilidades, respostas=respostas, checklist=checklist_row, readonly=True)

@app.route('/editar-checklist/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_checklist(id):
    db = get_db()
    habilidades = get_habilidades()
    total_itens = sum(len(cat['itens']) for cat in habilidades)
    
    if request.method == 'POST':
        respostas, itens_respondidos = process_checklist_form(request.form)
        status = 'Concluído' if itens_respondidos == total_itens else 'Incompleto'
        db.execute('''
            UPDATE checklists SET data_inicio=?, data_termino=?, respostas=?, status=?
            WHERE id=?
        ''', (request.form['data_inicio'], request.form['data_termino'], json.dumps(respostas), status, id))
        db.commit()
        return redirect(url_for('painel'))
    
    checklist_row = db.execute('SELECT * FROM checklists WHERE id = ?', (id,)).fetchone()
    aprendiz = db.execute('SELECT * FROM aprendizes WHERE id = ?', (checklist_row['aprendiz_id'],)).fetchone()
    respostas = json.loads(checklist_row['respostas'])
    return render_template('checklist.html', aprendiz=aprendiz, habilidades=habilidades, respostas=respostas, checklist=checklist_row)

@app.route('/excluir-checklist/<int:id>', methods=['POST'])
@login_required
def excluir_checklist(id):
    db = get_db()
    db.execute('DELETE FROM checklists WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('painel'))

@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    db = get_db()
    
    msg = None
    msg_type = "success"
    
    if request.method == 'POST':
        if 'nova_senha' in request.form:
            nova_senha = request.form['nova_senha']
            confirmar_senha = request.form['confirmar_senha']
            if nova_senha and nova_senha == confirmar_senha:
                hashed_pw = generate_password_hash(nova_senha)
                db.execute('UPDATE usuarios SET password_hash = ? WHERE id = ?', (hashed_pw, session['user_id']))
                db.commit()
                msg = "Senha atualizada com sucesso!"
            else:
                msg = "As senhas não coincidem ou estão vazias."
                msg_type = "error"

    usuarios = []
    if session.get('cargo') == 'Administrador':
        usuarios = db.execute('SELECT id, username, nome, cargo, strftime("%d/%m/%Y", criado_em) as data_formatada FROM usuarios ORDER BY criado_em DESC').fetchall()
        
    return render_template('configuracoes.html', usuarios=usuarios, msg=msg, msg_type=msg_type)

@app.route('/excluir-usuario/<int:id>', methods=['POST'])
@login_required
def excluir_usuario(id):
    if session.get('cargo') != 'Administrador':
        return redirect(url_for('painel'))
    db = get_db()
    if id != session['user_id']:
        db.execute('DELETE FROM usuarios WHERE id = ?', (id,))
        db.commit()
    return redirect(url_for('configuracoes'))

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
