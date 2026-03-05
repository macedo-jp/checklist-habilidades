from . import db
from datetime import datetime


class Crianca(db.Model):
    __tablename__ = 'criancas'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    data_nascimento = db.Column(db.Date, nullable=False)
    diagnostico = db.Column(db.String(255))
    psicologo_responsavel = db.Column(db.String(100))
    observacoes_gerais = db.Column(db.Text)
    
    avaliacoes = db.relationship('Avaliacao', backref='paciente', lazy=True, cascade="all, delete-orphan")


class Habilidade(db.Model):
    __tablename__ = 'habilidades'
    id = db.Column(db.Integer, primary_key=True)
    categoria = db.Column(db.String(100), nullable=False) # Ex: Habilidades de Atenção
    nome = db.Column(db.String(150), nullable=False)      # Ex: Contato Visual
    descricao = db.Column(db.Text)

    treinamentos = db.relationship('Treinamento', backref='habilidade', lazy=True)


class Avaliacao(db.Model):
    __tablename__ = 'avaliacoes'
    id = db.Column(db.Integer, primary_key=True)
    data_inicio = db.Column(db.DateTime, default=datetime.utcnow)
    data_termino = db.Column(db.DateTime, nullable=True)
    
    crianca_id = db.Column(db.Integer, db.ForeignKey('criancas.id'), nullable=False)
    
    respostas = db.relationship('RespostaAvaliacao', backref='avaliacao', lazy=True, cascade="all, delete-orphan")


class RespostaAvaliacao(db.Model):
    __tablename__ = 'respostas_avaliacao'
    id = db.Column(db.Integer, primary_key=True)
    avaliacao_id = db.Column(db.Integer, db.ForeignKey('avaliacoes.id'), nullable=False)
    habilidade_id = db.Column(db.Integer, db.ForeignKey('habilidades.id'), nullable=False)
    
    status = db.Column(db.Integer, nullable=False) 
    observacao_especifica = db.Column(db.Text)


class Treinamento(db.Model):
    __tablename__ = 'treinamentos'
    id = db.Column(db.Integer, primary_key=True)
    habilidade_id = db.Column(db.Integer, db.ForeignKey('habilidades.id'), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    descricao_atividade = db.Column(db.Text, nullable=False)
