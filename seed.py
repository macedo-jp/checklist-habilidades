from app import create_app, db
from app.models import Habilidade

def seed_habilidades():
    app = create_app()
    with app.app_context():
        habilidades_tea = {
            "Habilidades de Atenção": [
                "Sentar", "Esperar", "Contato Visual"
            ],
            "Habilidades de Imitação": [
                "Imitar movimentos motores grossos", 
                "Imitar ações com objetos"
            ],
            "Habilidades de Ouvinte": [
                "Seguir instruções de um passo", 
                "Identificar objetos", 
                "Identificar figuras", 
                "Identificar partes do corpo"
            ],
            "Habilidades Verbais": [
                "Apontar para itens desejados", 
                "Produzir sons com função comunicativa", 
                "Pedir vocalmente por coisas", 
                "Nomear partes do corpo", 
                "Nomear objetos", 
                "Nomear figuras"
            ],
            "Habilidades de Percepção Visual e Emparelhamento": [
                "Coordenação olho mão", 
                "Emparelhar objetos", 
                "Emparelhar figuras"
            ],
            "Habilidades de Brincar": [
                "Exploração de objetos", 
                "Dá função para o objeto"
            ]
        }
        
        for categoria, itens in habilidades_tea.items():
            for item in itens:
                existe = Habilidade.query.filter_by(nome=item).first()
                if not existe:
                    nova_habilidade = Habilidade(
                        nome=item,
                        categoria=categoria,
                        descricao=f"Avaliação da habilidade: {item}"
                    )
                    db.session.add(nova_habilidade)
        
        db.session.commit()

if __name__ == "__main__":
    seed_habilidades()
