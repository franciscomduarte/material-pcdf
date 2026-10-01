"""
conferir.py -- mostra em que PONTO DE CONTROLE da demonstração você está e DESENHA o grafo como ele está agora.

    python demo_cofre\\conferir.py

Roda os 5 pontos em ordem, marca ✓ / ✗ e, no primeiro que falhar, diz o que o teste encontrou e o que fazer.
No final imprime o MERMAID do grafo montado até agora (e salva em demo_cofre/saida/grafo_atual.mmd e .md):
cole o .mmd em https://mermaid.live, ou abra o .md no preview do VS Code, para VER o grafo crescer a cada ponto.

Para conferir a solução do professor:  $env:DESAFIO_DIR = "demo_cofre\\solucao"
"""
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.stdout.reconfigure(encoding="utf-8")

import test_pontos  # noqa: E402  (importar já carrega o seu main.py)

PASTA_SAIDA = Path(__file__).resolve().parent / "saida"


def executar_ponto(classe) -> tuple[bool, str]:
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(classe)
    resultado = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(suite)
    if resultado.wasSuccessful():
        return True, ""
    problemas = resultado.failures + resultado.errors
    detalhe = problemas[0][1].strip().splitlines()
    return False, detalhe[-1] if detalhe else "falhou"


def traduzir(erro: str) -> str | None:
    """Explica em português os erros mais comuns (devolve None se não reconhecer)."""
    if "must have an entrypoint" in erro:
        return ("o grafo ainda não tem nenhuma ligação com o START. Faça o PONTO 1: escreva a função receber (Fase A) e "
                "escreva add_node(\"receber\", receber) e add_edge(START, \"receber\") (Fase B).")
    if "unknown node" in erro:
        return ("uma aresta aponta para um nó que não foi registrado. Todo nó usado em add_edge ou no mapa de "
                "add_conditional_edges precisa de add_node antes.")
    if "KeyError" in erro:
        return ("o roteador devolveu um rótulo que não está no mapa de add_conditional_edges. "
                "Compare, letra a letra, o retorno do roteador com as chaves do dicionário.")
    if "GraphRecursionError" in erro or "Recursion limit" in erro:
        return ("o ciclo não para. Confira a condição de parada (PONTO 5): o roteador deve devolver 'bloquear' "
                "quando estado['tentativas'] >= MAX_TENTATIVAS.")
    if "IndexError" in erro:
        return "a lista de entradas acabou: use '' quando não houver mais senhas (estado['entradas'] pode ser menor que tentativas)."
    if "has no attribute" in erro or "is not defined" in erro:
        return "um nome usado no código não existe: confira a grafia das funções e dos campos do estado."
    return None


def mostrar_grafo_atual(ponto_atual: int | None) -> None:
    """Imprime (e salva) o Mermaid do grafo montado até agora. Se ainda não compila, explica."""
    print("\n" + "=" * 70)
    print("GRAFO COMO ESTÁ AGORA" + (f" (você está no ponto {ponto_atual})" if ponto_atual else " (completo)"))
    print("=" * 70)
    try:
        mermaid = test_pontos.cofre.construir_grafo().get_graph().draw_mermaid()
    except Exception as erro:  # o grafo pode estar incompleto
        print(f"(ainda não dá para desenhar: {type(erro).__name__}: {str(erro)[:150]})")
        print("O desenho aparece assim que o grafo compilar (PONTO 1: START -> receber).")
        return
    PASTA_SAIDA.mkdir(exist_ok=True)
    (PASTA_SAIDA / "grafo_atual.mmd").write_text(mermaid, encoding="utf-8")
    (PASTA_SAIDA / "grafo_atual.md").write_text(f"# Grafo atual\n\n```mermaid\n{mermaid}\n```\n", encoding="utf-8")
    print(mermaid)
    print("Para VER: cole o texto acima em https://mermaid.live, ou abra demo_cofre/saida/grafo_atual.md no preview do VS Code")


def main() -> None:
    print("PONTOS DE CONTROLE DA DEMONSTRAÇÃO (O COFRE)\n")
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
        print("Todos os 5 pontos passaram. Rode o grafo completo:")
        print("    python demo_cofre\\main.py")
        mostrar_grafo_atual(None)
        return
    i, titulo, dica, erro = proximo
    print(f"Você está no PONTO {i}: {titulo}")
    explicacao = traduzir(erro)
    if explicacao:
        print(f"  O que aconteceu: {explicacao}")
        print(f"  (mensagem técnica: {erro})")
    else:
        print(f"  O teste encontrou: {erro}")
    print(f"  O que fazer: {dica}")
    print(f"  Testar só este ponto: python -m unittest demo_cofre.test_pontos.Ponto{i} -v")
    mostrar_grafo_atual(i)


if __name__ == "__main__":
    main()
