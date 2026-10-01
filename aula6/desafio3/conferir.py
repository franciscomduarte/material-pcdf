"""
conferir.py -- mostra em que PONTO DE CONTROLE do desafio 3 você está e DESENHA o grafo como ele está agora.

    python desafio3\\conferir.py

Roda os 6 pontos em ordem (com o JevMock: sem internet e SEM gastar créditos do JEV), marca ✓ / ✗ e, no primeiro que
falhar, diz o que o teste encontrou e o que fazer. No final imprime o MERMAID do grafo montado até agora (e salva em
desafio3/saida/grafo_atual.mmd e .md): cole o .mmd em https://mermaid.live, ou abra o .md no preview do VS Code.
Ao terminar, mostra também o grafo colorido pelo TIPO de cada nó (JEV, LLM, tool, função).

Para conferir a solução do professor:  $env:DESAFIO_DIR = "desafio3\\solucao"
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
    if "NotImplementedError" in erro:
        return "construir_grafo() ainda não foi implementada. Comece pelo PONTO 1 (veja o docstring em main.py)."
    if "must have an entrypoint" in erro:
        return ("o grafo ainda não tem nenhuma ligação com o START. Faça o PONTO 1: escreva a função receber (Fase A) e "
                "descomente/escreva add_node(\"receber\", receber) e add_edge(START, \"receber\") (Fase B).")
    if "name 'jev' is not defined" in erro or "name 'modelo' is not defined" in erro:
        return ("a função usa `jev` ou `modelo` mas está FORA de construir_grafo. Coloque-a dentro, com a mesma indentação "
                "dos placeholders (é lá que eles existem).")
    if "unknown node" in erro:
        return ("uma aresta aponta para um nó que não foi registrado. Todo nó usado em add_edge ou no mapa de "
                "add_conditional_edges precisa de add_node antes.")
    if "KeyError" in erro:
        return ("um nome de campo ou de rótulo não existe: confira, letra a letra, os campos do Estado, as chaves de "
                "respostas[...] ('noul', 'choice', 'confidence') e os rótulos do mapa de add_conditional_edges.")
    if "has no attribute" in erro or "is not defined" in erro:
        return "um nome usado no código não existe: confira a grafia das funções e dos campos do estado."
    return None


def mostrar_grafo_atual(ponto_atual: int | None) -> None:
    """Imprime (e salva) o Mermaid do grafo montado até agora. Se ainda não compila, explica."""
    print("\n" + "=" * 70)
    print("GRAFO COMO ESTÁ AGORA" + (f" (você está no ponto {ponto_atual})" if ponto_atual else " (completo)"))
    print("=" * 70)
    try:
        app = test_pontos.desafio.construir_grafo(test_pontos.ModeloMock(), test_pontos.JevMock())
        mermaid = app.get_graph().draw_mermaid()
    except Exception as erro:  # o grafo pode estar incompleto
        print(f"(ainda não dá para desenhar: {type(erro).__name__}: {str(erro)[:150]})")
        print("O desenho aparece assim que o grafo compilar (PONTO 1: START -> receber).")
        return
    PASTA_SAIDA.mkdir(exist_ok=True)
    (PASTA_SAIDA / "grafo_atual.mmd").write_text(mermaid, encoding="utf-8")
    (PASTA_SAIDA / "grafo_atual.md").write_text(f"# Grafo atual\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print(mermaid)
    print("Para VER: cole o texto acima em https://mermaid.live, ou abra desafio3/saida/grafo_atual.md no preview do VS Code")
    if ponto_atual is None and hasattr(test_pontos.desafio, "mermaid_por_tipo"):
        por_tipo = test_pontos.desafio.mermaid_por_tipo(app)
        (PASTA_SAIDA / "grafo_por_tipo.mmd").write_text(por_tipo, encoding="utf-8")
        (PASTA_SAIDA / "grafo_por_tipo.md").write_text(f"# Grafo por tipo de nó\n\n```mermaid\n{por_tipo}\n```\n", encoding="utf-8")
        print("\n" + "=" * 70)
        print("O MESMO GRAFO, COLORIDO PELO TIPO DE NÓ: JEV (rosa) | LLM (azul) | tool (roxo) | função (cinza)")
        print("=" * 70)
        print(por_tipo)
        print("Salvo em desafio3/saida/grafo_por_tipo.mmd e .md")


def main() -> None:
    print(f"PONTOS DE CONTROLE DO DESAFIO 3 ({TOTAL} pontos)\n")
    proximo = None
    for i, (classe, titulo, dica) in enumerate(test_pontos.PONTOS, start=1):
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
        print(f"Todos os {TOTAL} pontos passaram. Rode as 5 perguntas (com o JEV real, 5 créditos):")
        print("    python desafio3\\main.py --perguntas")
        mostrar_grafo_atual(None)
        return
    i, titulo, dica, erro = proximo
    print(f"Você está no PONTO {i}: {titulo}")
    explicacao = traduzir(erro)
    if explicacao:
        print(f"  O que aconteceu: {explicacao}")
        if "NotImplementedError" not in erro:
            print(f"  (mensagem técnica: {erro})")
    else:
        print(f"  O teste encontrou: {erro}")
    print(f"  O que fazer: {dica}")
    print(f"  Testar só este ponto: python -m unittest desafio3.test_pontos.Ponto{i} -v")
    mostrar_grafo_atual(i)


if __name__ == "__main__":
    main()
