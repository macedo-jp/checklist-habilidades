# Sistema de Gestão Clínica

Este é um projeto desenvolvido para a disciplina de Projeto Integrador da Universidade Virtual do Estado de São Paulo (UNIVESP) para facilitar a gestão do checklist de habilidades básicas feitas em clínicas de reabilitação neurológica. O sistema permite o cadastro de terapeutas, aprendizes (pacientes) e o acompanhamento do checklist de habilidades.

## Tecnologias utilizadas

*   **Backend:** Python 3 com [Flask](https://flask.palletsprojects.com/)
*   **Banco de Dados:** SQLite3
*   **Frontend:** HTML5, Jinja2 (Template Engine do Flask), e [Tailwind CSS](https://tailwindcss.com/) (via CDN)
*   **Ícones:** Lucide Icons

## Pré-requisitos

Para rodar este projeto na sua máquina, você precisará apenas do **Python 3.11+** e do **pip** (gerenciador de pacotes do Python) instalados. Não é necessário configurar um servidor de banco de dados externo, pois o projeto utiliza SQLite.

## Como executar o projeto

Siga o passo a passo abaixo para rodar o sistema localmente:

### 1. Clonar ou baixar o repositório
Baixe os arquivos deste projeto para uma pasta no seu computador.

### 2. Abrir o terminal
Abra o terminal (ou prompt de comando) e navegue até a pasta onde o projeto foi extraído.

### 3. Criar um ambiente virtual (opcional, mas recomendado)
Para não conflitar com outras bibliotecas do seu computador, crie um ambiente virtual:
```bash
# No Windows:
python -m venv venv
venv\Scripts\activate

# No Linux/Mac:
python3 -m venv venv
source venv/bin/activate
```

### 4. Instalar as dependências
Com o ambiente ativado (ou diretamente na sua máquina, caso tenha pulado o passo anterior), instale os pacotes necessários:
```bash
pip install -r requirements.txt
```

### 5. Configurar as variáveis de ambiente (opcional)
Você pode criar um arquivo chamado `.env` na raiz do projeto copiando o `.env.example`:
```bash
cp .env.example .env
```
O sistema funcionará caso você ignore esta etapa, utilizando valores padrão seguros para o ambiente de desenvolvimento.

### 6. Iniciar a aplicação
Execute o arquivo principal para iniciar o servidor:
```bash
python app.py
# ou 
python3 app.py
```

### 7. Acessar o sistema
Abra o seu navegador web favorito e digite o seguinte endereço:
```text
http://127.0.0.1:3000
```

## Acesso padrão (Administrador)

Ao iniciar a aplicação pela primeira vez, o banco de dados (`clinica_v1.db`) é gerado automaticamente e uma conta de administrador padrão é criada para que você possa avaliar o projeto:

*   **Usuário (Username):** `root`
*   **Senha:** `root123!`

**Importante:** Faça o login com essas credenciais. Como este usuário é um Administrador, ele tem a permissão de criar outros terapeutas e usuários regulares a partir da guia de configurações.

## Organização do código

*   `app.py`: Arquivo principal contendo toda a lógica do servidor, rotas da aplicação (MVC - Controllers), lógica de banco de dados e autenticação.
*   `templates/`: Diretório contendo os arquivos HTML de interface, processados pelo Jinja2 (MVC - Views).
*   `requirements.txt`: Lista de pacotes dependências do Python.
*   `.env.example`: Exemplo de configuração de variáveis de ambiente do servidor.

## Exportação e importação em massa (CSV)
A plataforma conta com um gestor de exportação e importação. Os dados da aplicação (Terapeutas, Aprendizes e check-lists) podem ser facilmente salvos num arquivo `.csv` e lidos por programas como Microsoft Excel, Google Sheets, etc.
É possível atualizar a base de dados enviando planilhas CSV desde que elas respeitem as colunas exportadas pela própria plataforma. Isso facilita a migração rápida de muitos aprendizes ou registros.

## Notas sobre deploy
*   **Banco de Diretorios & SQLite:** O SQLite armazena os dados no arquivo local (ex: `clinica_v1.db`). Ao dar deploy ou recriar containers, cuide para prover um arquivo como volume persistido.
*   **Flask Development Server:** O servidor iniciado via `app.run()` é recomentado apenas para desenvolvimento. Para rodar em produção com requisições simultâneas e maior escalabilidade, utilize servidores WSGI/ASGI como `gunicorn` ou `waitress`.
*   **SECRET_KEY:** Lembre-se de definir a variável de ambiente `SECRET_KEY` para uma chave forte, segura e randômica quando for implantar a aplicação de verdade.
