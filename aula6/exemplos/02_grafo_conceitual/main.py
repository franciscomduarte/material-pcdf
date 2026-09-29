"""
Exemplo 02 -- GRAFO CONCEITUAL (Python puro).

No exemplo anterior o fluxo estava "escondido" na ordem das chamadas.
Agora vamos escrever o PROCESSO COMO DADO:

    NÓ     = uma etapa do processo
    ARESTA = um caminho de uma etapa para outra

    receber -> classificar -> analisar -> responder

Ainda é o mesmo fluxo linear, mas agora ele é uma estrutura que podemos
inspecionar, desenhar e -- na segunda parte -- modificar.

Rodar:
    python main.py
"""

# dicionário: chave = nó, valor = lista dos nós para onde há aresta
grafo_linear = {
    "receber": ["classificar"],
    "classificar": ["analisar"],
    "analisar": ["responder"],
    "responder": [],  # sem saída: fim do processo
}

print("=== Grafo linear (lista de arestas) ===")
for no, proximos in grafo_linear.items():
    print(f"{no} -> {proximos}")

print("\n=== Percorrendo o grafo a partir de 'receber' ===")
atual = "receber"
caminho = [atual]
while grafo_linear[atual]:
    atual = grafo_linear[atual][0]  # só há um caminho possível
    caminho.append(atual)
print(" -> ".join(caminho))

# ---------------------------------------------------------------------------
# A VANTAGEM: agora o mesmo formato aceita DECISÃO.
# 'classificar' passa a ter DUAS arestas de saída (um branch):
#
#                  ┌──> responder                          (simples)
#   classificar ───┤
#                  └──> pesquisar -> analisar -> responder (complexa)
# ---------------------------------------------------------------------------
grafo_com_decisao = {
    "receber": ["classificar"],
    "classificar": ["responder", "pesquisar"],
    "pesquisar": ["analisar"],
    "analisar": ["responder"],
    "responder": [],
}

print("\n=== Grafo com decisão ===")
for no, proximos in grafo_com_decisao.items():
    print(f"{no} -> {proximos}")

# Um nó com mais de uma saída é um ponto de decisão.
print("\nPontos de decisão (nós com mais de uma saída):")
for no, proximos in grafo_com_decisao.items():
    if len(proximos) > 1:
        print(f"  {no} escolhe entre {proximos}")

# ---------------------------------------------------------------------------
# E se houver caminho de volta? ('revisar' aponta para 'analisar')
# Isso é um CICLO. Vamos detectar um, à mão, só para fixar o conceito.
# ---------------------------------------------------------------------------
grafo_com_ciclo = {
    "analisar": ["validar"],
    "validar": ["responder", "revisar"],
    "revisar": ["analisar"],  # volta!
    "responder": [],
}


def tem_ciclo(grafo):
    """Busca em profundidade: se voltamos a um nó do caminho atual, há ciclo."""

    def visita(no, caminho):
        if no in caminho:
            return True
        return any(visita(p, caminho + [no]) for p in grafo[no])

    return any(visita(no, []) for no in grafo)


print("\n=== Detecção de ciclo ===")
print("grafo_linear      tem ciclo?", tem_ciclo(grafo_linear))
print("grafo_com_decisao tem ciclo?", tem_ciclo(grafo_com_decisao))
print("grafo_com_ciclo   tem ciclo?", tem_ciclo(grafo_com_ciclo))
print("\nSem ciclo + arestas com direção = DAG. Com ciclo, precisamos de condição de parada.")
