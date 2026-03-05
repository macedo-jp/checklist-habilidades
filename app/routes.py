from flask import render_template, request, redirect, url_for, flash
from . import db
from .models import Crianca, Habilidade, Avaliacao, RespostaAvaliacao
from flask import current_app as app

@app.route('/')
def index():
    # Busca todas as crianças para listar na página inicial
    criancas = Crianca.query.all()
    return render_template('index.html', criancas=criancas)

@app.route('/nova_avaliacao/<int:crianca_id>', methods=['GET', 'POST'])
def nova_avaliacao(crianca_id):
    crianca = Crianca.query.get_or_404(crianca_id)
    habilidades = Habilidade.query.all()

    if request.method == 'POST':
        nova_aval = Avaliacao(crianca_id=crianca.id)
        db.session.add(nova_aval)
        db.session.flush() 

        for hab in habilidades:
            status = request.form.get(f'hab_{hab.id}')
            obs = request.form.get(f'obs_{hab.id}')
            
            if status:
                resposta = RespostaAvaliacao(
                    avaliacao_id=nova_aval.id,
                    habilidade_id=hab.id,
                    status=int(status),
                    observacao_especifica=obs
                )
                db.session.add(resposta)
        
        db.session.commit()
        flash(f"Avaliação de {crianca.nome} salva com sucesso!", "success")
        return redirect(url_for('index'))

    # Agrupamento para o template
    categorias = {}
    for h in habilidades:
        if h.categoria not in categorias:
            categorias[h.categoria] = []
        categorias[h.categoria].append(h)

    return render_template('avaliacao.html', crianca=crianca, categorias=categorias)

# ADICIONE ESTA PARTE AGORA:
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_crianca():
    if request.method == 'POST':
        # Captura os dados do formulário HTML
        nome = request.form.get('nome')
        nascimento = request.form.get('nascimento')
        psicologo = request.form.get('psicologo')

        nova_crianca = Crianca(
            nome=nome,
            data_nascimento=nascimento,
            psicologo_responsavel=psicologo
        )
        
        db.session.add(nova_crianca)
        db.session.commit()
        
        flash("Criança cadastrada com sucesso!", "success")
        return redirect(url_for('index'))
    

@app.route('/editar_avaliacao/<int:avaliacao_id>', methods=['GET', 'POST'])
def editar_avaliacao(avaliacao_id):
    # Busca a avaliação ou retorna 404 se não existir
    avaliacao = Avaliacao.query.get_or_404(avaliacao_id)
    crianca = avaliacao.paciente
    habilidades = Habilidade.query.all()
    
    # Criamos um dicionário para mapear as respostas atuais: {habilidade_id: status}
    respostas_atuais = {r.habilidade_id: r for r in avaliacao.respostas}

    if request.method == 'POST':
        for hab in habilidades:
            status = request.form.get(f'hab_{hab.id}')
            obs = request.form.get(f'obs_{hab.id}')
            
            # Se já existia uma resposta, atualizamos. Se não, criamos uma nova.
            if hab.id in respostas_atuais:
                respostas_atuais[hab.id].status = int(status) if status else 0
                respostas_atuais[hab.id].observacao_especifica = obs
            elif status:
                nova_resp = RespostaAvaliacao(
                    avaliacao_id=avaliacao.id,
                    habilidade_id=hab.id,
                    status=int(status),
                    observacao_especifica=obs
                )
                db.session.add(nova_resp)
        
        db.session.commit()
        flash(f"Avaliação de {crianca.nome} atualizada com sucesso!", "success")
        return redirect(url_for('index'))

    # Organiza para o template (mesma lógica da rota de criação)
    categorias = {}
    for h in habilidades:
        if h.categoria not in categorias:
            categorias[h.categoria] = []
        categorias[h.categoria].append(h)

    return render_template('editar_avaliacao.html', 
                           avaliacao=avaliacao, 
                           crianca=crianca, 
                           categorias=categorias, 
                           respostas_atuais=respostas_atuais)
        
    return render_template('cadastrar_crianca.html')
