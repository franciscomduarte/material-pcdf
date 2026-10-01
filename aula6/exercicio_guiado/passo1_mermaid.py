"""
PASSO 1 -- Do grafo ao desenho (Mermaid).

    python passo1_mermaid.py                 # usa o exemplo 10_agente_completo
    python passo1_mermaid.py 07_dag          # ou outro exemplo

Complete os TODOs (leia o README.md, passo 1). Ao final o script deve:
  - imprimir o Mermaid do grafo;
  - salvar saida/<exemplo>.mmd  (só o texto Mermaid, para colar em https://mermaid.live);
  - salvar saida/<exemplo>.md   (o mesmo Mermaid dentro de um bloco ```mermaid, para o preview do VS Code).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from carregar_grafo import carregar_app

exemplo = sys.argv[1] if len(sys.argv) > 1 else "10_agente_completo"

# TODO 1: carregue o grafo compilado do exemplo (use carregar_app).
app = None

# TODO 2: peça ao LangGraph o Mermaid do grafo (dica: app.get_graph().draw_mermaid()).
mermaid = ""

pasta_saida = Path(__file__).resolve().parent / "saida"
pasta_saida.mkdir(exist_ok=True)

# TODO 3: salve `mermaid` em saida/<exemplo>.mmd  (Path.write_text, encoding="utf-8").

# TODO 4: salve em saida/<exemplo>.md um título e o Mermaid dentro de um bloco de código:
#         # <exemplo>
#
#         ```mermaid
#         ...aqui o Mermaid...
#         ```

print(mermaid)
print(f"\nSalvo em saida/{exemplo}.mmd e saida/{exemplo}.md")
