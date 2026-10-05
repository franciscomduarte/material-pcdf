"""
Compara o desafio 2 SEM modelo de decisão (o nó extrair é o LLM) e COM modelo de decisão (o nó extrair é o JEV ou o Laya),
nas mesmas ocorrências.

    python desafio2\\comparar_jev\\comparar.py

Cada ocorrência roda nos dois grafos. O quadro final mostra, lado a lado: a gravidade, o bairro, o caminho, quantas
chamadas ao LLM e ao JEV (1 crédito cada) e o tempo. Precisa de OPENAI_API_KEY (ou Ollama) e de UM decisor:
    JEV real  -> JEV_AI_API_KEY no .env (1 crédito por ocorrência)
    Laya      -> $env:JEV = "laya"   (pip install laya; roda local, sem chave e sem créditos)
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from grafo import construir_grafo, executar  # noqa: E402
from jev import obter_jev  # noqa: E402
from provedor import obter_modelo_real  # noqa: E402

# as 5 ocorrências do desafio 2 + 3 que testam o que o JEV muda (acento, bairro ambíguo, vocabulário diferente)
OCORRENCIAS = [
    "Assalto em andamento em Taguatinga, preciso de uma viatura",
    "Homem ferido em briga em Sobradinho",
    "Tiro disparado no Gama",
    "Barulho excessivo em festa na Asa Sul",
    "Preciso de ajuda urgente",
    "Briga de vizinhos com faca em Ceilandia, tem gente machucada",         # sem acento: o LLM costuma copiar assim
    "Furto de bicicleta em Taguatinga ou Ceilândia, não lembro direito",    # bairro ambíguo: adivinhar ou perguntar?
    "Meu vizinho está ameaçando a família com uma arma na Asa Norte",       # gravidade sem as palavras 'assalto'/'tiro'
]


class Contador:
    """Conta as chamadas feitas ao LLM (gerar) ou ao JEV (decidir), sem alterar o comportamento."""

    def __init__(self, interno, metodo: str):
        self._interno, self._metodo, self.chamadas = interno, metodo, 0
        self.nome = getattr(interno, "nome", "")

    def __getattr__(self, nome):
        if nome == self._metodo:
            def chamar(*args, **kwargs):
                self.chamadas += 1
                return getattr(self._interno, nome)(*args, **kwargs)
            return chamar
        return getattr(self._interno, nome)


def rodar(ocorrencia: str, com_jev: bool, modelo_real, jev_real):
    llm = Contador(modelo_real, "gerar")
    jev = Contador(jev_real, "decidir") if com_jev else None
    app = construir_grafo(llm, jev)
    inicio = time.perf_counter()
    estado, caminho = executar(app, ocorrencia)
    return {"estado": estado, "caminho": caminho, "llm": llm.chamadas, "jev": jev.chamadas if jev else 0,
            "segundos": time.perf_counter() - inicio}


def resumo_caminho(caminho):
    """Só o que difere: o desvio (onde terminou) e se houve apoio ou ciclo de revisão."""
    fim = caminho[-1]
    extras = []
    if "acionar_apoio" in caminho:
        extras.append("apoio")
    if "revisar" in caminho:
        extras.append(f"{caminho.count('revisar')}x revisão")
    return fim + (f" (+{', '.join(extras)})" if extras else "")


if __name__ == "__main__":
    jev_real = obter_jev()  # JEV real ou Laya local; sem nenhum dos dois, o programa para
    modelo = obter_modelo_real()
    print(f"LLM: {modelo.nome} | decisões: {jev_real.nome}\n")

    linhas = []
    for i, ocorrencia in enumerate(OCORRENCIAS, start=1):
        print(f"[{i}/{len(OCORRENCIAS)}] {ocorrencia}")
        sem = rodar(ocorrencia, False, modelo, jev_real)
        com = rodar(ocorrencia, True, modelo, jev_real)
        linhas.append((ocorrencia, sem, com))
        for rotulo, r in (("SEM MODELO DE DECISÃO", sem), ("COM MODELO DE DECISÃO", com)):
            e = r["estado"]
            certeza = ""
            if e.get("p_grave", -1) >= 0:
                certeza = f" p_grave={e['p_grave']:.2f} confiança_bairro={e['confianca_bairro']:.2f}"
            print(f"    {rotulo:22}: gravidade={e.get('gravidade')!r} bairro={e.get('bairro')!r}{certeza}")
            print(f"{' ' * 28}termina em {resumo_caminho(r['caminho'])} | LLM {r['llm']} chamada(s), modelo de decisão {r['jev']} | {r['segundos']:.1f}s")

    print("\n" + "=" * 120)
    print(f"{'ocorrência':44} | {'SEM MODELO DE DECISÃO (LLM extrai)':48} | COM MODELO DE DECISÃO")
    print("-" * 120)
    for ocorrencia, sem, com in linhas:
        a = f"{sem['estado'].get('gravidade')}/{sem['estado'].get('bairro') or '-'} -> {sem['caminho'][-1]}"
        b = f"{com['estado'].get('gravidade')}/{com['estado'].get('bairro') or '-'} -> {com['caminho'][-1]}"
        print(f"{ocorrencia[:44]:44} | {a:48} | {b}")
    t_sem, t_com = sum(s['segundos'] for _, s, _ in linhas), sum(c['segundos'] for _, _, c in linhas)
    l_sem, l_com = sum(s['llm'] for _, s, _ in linhas), sum(c['llm'] for _, _, c in linhas)
    print("-" * 120)
    print(f"Chamadas ao LLM: {l_sem} sem modelo de decisão x {l_com} com modelo de decisão | chamadas ao modelo de decisão: {len(linhas)} | tempo: {t_sem:.0f}s x {t_com:.0f}s")
