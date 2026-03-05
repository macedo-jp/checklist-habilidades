# checklist-habilidades
Aplicação para mapear habilidades básicas em crianças com TEA

Aqui está o README.md em uma versão mais limpa e direta, utilizando apenas Markdown padrão e removendo os ícones e emojis para um visual mais sóbrio.
Sistema de Monitoramento de Habilidades (TEA)

Esta aplicação web auxilia psicólogos no levantamento de déficits em habilidades básicas em crianças com potencial Transtorno do Espectro Autista (TEA). O sistema permite o registro de avaliações baseadas em protocolos clínicos, acompanhamento do histórico e edição de dados.
Funcionalidades

    Gestão de Pacientes: Cadastro e organização de perfis infantis.

    Checklist Dinâmico: Formulário de avaliação baseado no protocolo de "Ensino de Habilidades Básicas".

    Histórico e Edição: Visualização de avaliações anteriores com opção de alteração de dados.

    Banco de Dados: Armazenamento estruturado em PostgreSQL.

    Segurança: Configurações sensíveis isoladas em variáveis de ambiente.

Tecnologias

    Backend: Python (Flask)

    Banco de Dados: PostgreSQL com SQLAlchemy (ORM)

    Frontend: HTML5, Bootstrap 5

    Gestão de Ambiente: Python-dotenv

Instalação e Configuração
1. Preparação do Ambiente
Bash

git clone https://github.com/seu-usuario/projeto-tea.git
cd projeto-tea
python -m venv venv
# Ativar venv (Windows: venv\Scripts\activate | Linux: source venv/bin/activate)
pip install -r requirements.txt

2. Configuração do Banco de Dados

Crie um arquivo .env na raiz do projeto seguindo o modelo abaixo:
Plaintext

DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tea_db
SECRET_KEY=sua_chave_hexadecimal
FLASK_DEBUG=1

3. Inicialização

Após criar o banco no PostgreSQL, execute o script para carregar as habilidades do protocolo:
Bash

python seed.py

4. Execução
Bash

python run.py

A aplicação estará disponível em http://127.0.0.1:5000/.
Licença

Este projeto está sob a licença MIT.