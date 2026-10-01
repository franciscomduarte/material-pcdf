"""
conferir.py -- mostra em que PONTO DE CONTROLE do desafio você está e DESENHA o grafo como ele está agora.

    python desafio\\conferir.py

Roda os 10 pontos em ordem (PARTE A: 1 a 7; PARTE B: 8 a 10), marca ✓ / ✗ e, no primeiro que falhar, diz o que o
teste encontrou e o que fazer. Os pontos seguintes aparecem como "pendente" (um de cada vez é o bom ritmo).

No final imprime o MERMAID do grafo que você montou até agora (e salva em desafio/saida/grafo_atual.mmd e .md):
cole o .mmd em https://mermaid.live, ou abra o .md no preview do VS Code, para VER o grafo crescer a cada ponto.
Ao terminar a Parte B, mostra também o grafo colorido pelo TIPO de cada nó (LLM, MCP, API, tool, função).

Para conferir a solução do professor:  $env:DESAFIO_DIR = "desafio\\solucao"
"""
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

import test_pontos  # noqa: E402  (importar já carrega o seu main.py)

PASTA_SAIDA = Path(__file__).resolve().parent / "saida"
TOTAL = len(test_pontos.PONTOS)


def executar_ponto(classe) -> tuple[bool, str]:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(classe)
    resultado = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    if resultado.wasSuccessful():
        return True, ""
    problemas = resultado.failures + resultado.errors
    detalhe = problemas[0][1].strip().splitlines()
    return False, detalhe[-1] if detalhe else "falhou"


def traduzir(erro: str) -> str | None:
    """Explica em português os erros mais comuns do desafio (devolve None se não reconhecer)."""
    if "PONTO 10" in erro and "NotImplementedError" in erro:
        return "a tool somar_dias_uteis() ainda não foi escrita (topo do arquivo, seção PARTE B). É o ponto 10."
    if "NotImplementedError" in erro:
        return "construir_grafo() ainda não foi implementada. Comece pelo PONTO 1 (veja o docstring em main.py)."
    if "must have an entrypoint" in erro:
        return ("o grafo ainda não tem nenhuma ligação com o START. Faça o PONTO 1: escreva a função receber (Fase A) e "
                "descomente/escreva add_node(\"receber\", receber) e add_edge(START, \"receber\") (Fase B).")
    if "name 'modelo' is not defined" in erro:
        return ("a função usa `modelo` mas está FORA de construir_grafo. Coloque-a dentro, com a mesma indentação "
                "dos placeholders (é lá que `modelo` existe).")
    if "unknown node" in erro:
        return ("uma aresta aponta para um nó que não foi registrado. Confira os nomes: todo nó usado em add_edge "
                "ou no mapa de add_conditional_edges precisa de add_node antes.")
    if "Connection closed" in erro or "No module named 'mcp'" in erro:
        return ("o MCP Server não subiu. Confira se o pacote mcp está instalado (`pip install -r requirements.txt` com o "
                ".venv ativo) e se desafio/mcp_base.py existe. Nunca use print() dentro do servidor MCP.")
    if "KeyError" in erro:
        return ("um nome de campo ou de rótulo não existe: confira, letra a letra, os campos do Estado e as chaves do mapa "
                "de add_conditional_edges com o que o roteador devolve.")
    if "GraphRecursionError" in erro or "Recursion limit" in erro:
        return ("o ciclo não para. Confira a condição de parada (PONTO 7): o roteador de validar deve devolver "
                "'desistir' quando estado['tentativas'] >= MAX_TENTATIVAS.")
    if "has no attribute" in erro or "is not defined" in erro:
        return "um nome usado no código não existe: confira a grafia das funções e dos campos do estado."
    return None


def mostrar_grafo_atual(ponto_atual: int | None) -> None:
    """Imprime (e salva) o Mermaid do grafo montado até agora. Se ainda não compila, explica."""
    print("\n" + "=" * 70)
    titulo = "GRAFO COMO ESTÁ AGORA" + (f" (você está no ponto {ponto_atual})" if ponto_atual else " (completo)")
    print(titulo)
    print("=" * 70)
    try:
        app = test_pontos.desafio.construir_grafo(test_pontos.ModeloMock())
        mermaid = app.get_graph().draw_mermaid()
    except Exception as erro:  # o grafo pode estar incompleto
        print(f"(ainda não dá para desenhar: {type(erro).__name__}: {str(erro)[:150]})")
        print("O desenho aparece assim que o grafo compilar (PONTO 1: START -> receber).")
        return
    PASTA_SAIDA.mkdir(exist_ok=True)
    (PASTA_SAIDA / "grafo_atual.mmd").write_text(mermaid, encoding="utf-8")
    (PASTA_SAIDA / "grafo_atual.md").write_text(f"# Grafo atual\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print(mermaid)
    print("Para VER: cole o texto acima em https://mermaid.live, ou abra desafio/saida/grafo_atual.md no preview do VS Code")
    print("(salvo também em desafio/saida/grafo_atual.mmd).")
    if ponto_atual is None and hasattr(test_pontos.desafio, "mermaid_por_tipo"):
        por_tipo = test_pontos.desafio.mermaid_por_tipo(app)
        (PASTA_SAIDA / "grafo_por_tipo.mmd").write_text(por_tipo, encoding="utf-8")
        (PASTA_SAIDA / "grafo_por_tipo.md").write_text(f"# Grafo por tipo de nó\n\n```mermaid\n{por_tipo}\n```\n", encoding="utf-8")
        print("\n" + "=" * 70)
        print("O MESMO GRAFO, COLORIDO PELO TIPO DE NÓ: LLM (azul) | MCP (laranja) | API (verde) | tool (roxo) | função (cinza)")
        print("=" * 70)
        print(por_tipo)
        print("Salvo em desafio/saida/grafo_por_tipo.mmd e .md")


def main() -> None:
    print(f"PONTOS DE CONTROLE DO DESAFIO ({TOTAL} pontos: Parte A = 1 a 7, Parte B = 8 a 10)\n")
    proximo = None
    for i, (classe, titulo, dica) in enumerate(test_pontos.PONTOS, start=1):
        if i == 1:
            print("  PARTE A: decisão, ciclo e parada")
        if i == 8:
            print("  PARTE B: os tipos de nó (MCP, API, tool)")
        if proximo is not None:
            print(f"  ·  Ponto {i}: {titulo}   (pendente)")
            continue
        ok, erro = executar_ponto(classe)
        if ok:
            print(f"  ✓  Ponto {i}: {titulo}")
        else:
            print(f"  ✗  Ponto {i}: {titulo}")
            proximo = (i, titulo, dica, erro)
    print()
    if proximo is None:
        print(f"Todos os {TOTAL} pontos passaram. Rode o grafo completo e os testes finais da Parte A:")
        print("    python desafio\\main.py")
        print("    python -m unittest desafio.test_desafio -v")
        mostrar_grafo_atual(None)
        return
    i, titulo, dica, erro = proximo
    if i == 8:
        print("A PARTE A está completa (pontos 1 a 7). Agora a PARTE B: cada nó ganha o seu TIPO.")
    print(f"Você está no PONTO {i}: {titulo}")
    explicacao = traduzir(erro)
    if explicacao:
        print(f"  O que aconteceu: {explicacao}")
        if "NotImplementedError" not in erro:
            print(f"  (mensagem técnica: {erro})")
    else:
        print(f"  O teste encontrou: {erro}")
    print(f"  O que fazer: {dica}")
    print(f"  Testar só este ponto: python -m unittest desafio.test_pontos.Ponto{i} -v")
    mostrar_grafo_atual(i)


if __name__ == "__main__":
    main()
