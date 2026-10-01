"""
carregar_grafo.py -- JÁ VEM PRONTO (é encanamento, não é o foco do exercício).

Carrega o grafo compilado (`app`) de um exemplo da Aula 6 sem precisar rodar o exemplo:

    from carregar_grafo import EXEMPLOS, carregar_app
    app = carregar_app("10_agente_completo")
    app.get_graph()            # o grafo "desenhável" do LangGraph

Duas armadilhas que este arquivo resolve por você (leia, elas aparecem em qualquer MCP):

  1. Os exemplos 04 a 07 EXECUTAM o grafo ao serem importados (não têm `if __name__`) e
     imprimem na tela. Num MCP Server stdio, o stdout é o CANAL DO PROTOCOLO: qualquer print
     estraga a conversa com o cliente. Por isso a importação roda dentro de redirect_stdout.
  2. Cada exemplo tem o seu `modelo_mock.py`, todos com o mesmo nome de módulo. Sem limpar
     `sys.modules`, o 2º exemplo carregado usaria o Mock do 1º.
"""
import contextlib
import importlib.util
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # provedor.py

import provedor  # noqa: E402

PASTA_EXEMPLOS = Path(__file__).resolve().parents[1] / "exemplos"



class ModeloSoParaDesenhar(provedor.Modelo):
    """Os exemplos 09, 10 e 11 pedem um LLM real ao serem importados. Aqui só queremos DESENHAR o grafo (nenhum nó roda):
    este modelo existe só para a importação funcionar sem chave. Se alguém tentar usá-lo, ele avisa."""

    nome = "so-para-desenhar"

    def gerar(self, prompt: str) -> str:
        raise RuntimeError("Este modelo é só para desenhar o grafo; rode o main.py do exemplo para usar o LLM real.")


# Exemplos que expõem `app` no nível do módulo (o 08 monta o grafo dentro de funções).
EXEMPLOS = [
    "04_langgraph_basico",
    "05_multiplos_nos",
    "06_fluxo_condicional",
    "07_dag",
    "09_llm_no_grafo",
    "10_agente_completo",
    "11_grafo_real",
]


def carregar_app(exemplo: str):
    """Devolve o grafo compilado do exemplo. Levanta ValueError se o nome não existir."""
    if exemplo not in EXEMPLOS:
        raise ValueError(f"Exemplo desconhecido: {exemplo!r}. Opções: {', '.join(EXEMPLOS)}")
    pasta = str((PASTA_EXEMPLOS / exemplo).resolve())
    sys.modules.pop("modelo_mock", None)  # armadilha 2
    sys.path.insert(0, pasta)
    original = provedor.obter_modelo_real
    provedor.obter_modelo_real = lambda *args, **kwargs: ModeloSoParaDesenhar()  # o exemplo não exige chave só para ser desenhado
    try:
        with contextlib.redirect_stdout(io.StringIO()):  # armadilha 1
            spec = importlib.util.spec_from_file_location(f"exemplo_{exemplo}", Path(pasta) / "main.py")
            modulo = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(modulo)
    finally:
        provedor.obter_modelo_real = original
        sys.path.remove(pasta)
    return modulo.app
