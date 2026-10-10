"""
ETAPA 2 -- Extração estruturada do pedido (15 min) e 🆕 A -- votação em paralelo (10 min).

ESQUELETO: implemente as etapas na ordem (troque cada raise NotImplementedError pelo código da etapa).
  ETAPA 2.1 -- complete o modelo Pydantic `Pedido` (campos + Field(description=...))
  ETAPA 2.2 -- criar_extrator(): um Agent com output_type=Pedido
  ETAPA 2.3 -- extrair(): roda UM extrator e devolve um Pedido
  🆕 A.1    -- INSTRUCOES_VOTANTES: 3 instruções ligeiramente diferentes
  🆕 A.2    -- extrair_com_votacao(): os 3 extratores AO MESMO TEMPO (asyncio.gather)
  🆕 A.3    -- votar(): maioria por campo; sem maioria em tipo/datas -> divergencia=True
  🆕 A.4    -- no __main__: compare o tempo em paralelo x em sequência

REFERÊNCIAS NAS AULAS
  aula2/agente_output.py                   output_type com um BaseModel simples
  aula2/agente_output2.py                  Enum + listas + Field(description=...)          <- o mais parecido
  aula7/exemplos/08_paralelismo/main.py    🆕 A: o CONCEITO de paralelismo (lá: tarefas DIFERENTES para ganhar tempo;
                                           aqui: a MESMA tarefa 3 vezes para ganhar confiabilidade)
  aula3/agente_parada3.py                  Runner.run (assíncrono) dentro de asyncio, como em A.2
  aula3/agente_retry.py                    (volte aqui na Etapa 4.1 para injetar a data de hoje nas instruções)

Rodar:
    python extracao.py            # extrai C1, C2, C5 e C11
    python extracao.py --votacao  # 🆕 A: C1, C2 e C9 com 3 votos e o tempo medido

Pronto quando: C2 sai com dias_vendidos=10, C11 com tipo_destino="exterior", C5 com matricula=None;
               na votação, C1/C2 unânimes e C9 mostrando os votos.
"""
import asyncio
import sys
import time
from collections import Counter
from enum import Enum

from agents import Agent, Runner
from pydantic import BaseModel, Field

from dados.casos import CASOS
from provedor import configurar

MODELO = configurar()


class TipoPedido(str, Enum):
    FERIAS = "ferias"
    ABONO = "abono"
    DIARIA = "diaria"
    LICENCA_SAUDE = "licenca_saude"
    OUTRO = "outro"


class TipoDestino(str, Enum):
    CAPITAL = "capital"
    INTERIOR = "interior"
    EXTERIOR = "exterior"


class Pedido(BaseModel):
    # ETAPA 2.1 -- complete os campos. O primeiro já está pronto como modelo.
    #   matricula: str | None          (4 dígitos; None se o servidor não informou)
    #   data_inicio: str | None        (AAAA-MM-DD)
    #   data_fim: str | None           (AAAA-MM-DD; no abono, igual à data_inicio)
    #   dias_vendidos: int             (0 a 10; abono pecuniário, regra N2 -- use Field(default=0, ge=0, le=10, ...))
    #   destino: str | None            (só para diária: a cidade)
    #   tipo_destino: TipoDestino | None
    #   justificativa: str             (resumo do motivo, sem dados de saúde)
    #   Escreva a DESCRIPTION de cada um: é a "instrução" que o LLM lê para preencher o campo.
    #   Referência: aula2/agente_output2.py (Ocorrencia, Envolvido, PapelEnvolvido)
    tipo: TipoPedido = Field(description=(
        "Tipo do pedido: 'ferias' (descanso anual, pode incluir venda de dias), 'abono' (folga de 1 dia útil), "
        "'diaria' (viagem a serviço), 'licenca_saude' (afastamento por doença) ou 'outro'."))


def criar_extrator(instrucoes: str, input_guardrails: list | None = None) -> Agent:
    # ETAPA 2.2 -- devolva Agent(name="Extrator", instructions=instrucoes, output_type=Pedido,
    #   input_guardrails=input_guardrails or [])
    #   (os guardrails só entram na Etapa 3; até lá, a lista fica vazia)
    raise NotImplementedError("ETAPA 2.2: criar_extrator")


INSTRUCOES_EXTRATOR = (
    "Você extrai pedidos de servidores para o RH (férias, abono ou diária). "
    "TODO ETAPA 2.2: complete -- datas no formato AAAA-MM-DD, não invente o que não foi dito (use null), "
    "dias vendidos só se o servidor pedir explicitamente."
    # TODO ETAPA 4.1: acrescente aqui a data de hoje (ferramentas.texto_hoje()), como em aula3/agente_retry.py
)


def extrair(texto: str) -> Pedido:
    # ETAPA 2.3 -- rode criar_extrator(INSTRUCOES_EXTRATOR) com Runner.run_sync e devolva final_output
    #   (é um objeto Pedido, não texto!)
    raise NotImplementedError("ETAPA 2.3: extrair")


# ------------------------------------------------------------------ 🆕 A: votação
# 🆕 A.1 -- três instruções LIGEIRAMENTE diferentes para a MESMA tarefa
#   ex.: um extrator literal; um que confere as datas contra o calendário; um que "pensa como o RH".
INSTRUCOES_VOTANTES: list[str] = []  # TODO 🆕 A.1: preencha com 3 strings


async def extrair_com_votacao(texto: str) -> tuple[Pedido, bool, list[Pedido]]:
    # 🆕 A.2 -- crie os 3 extratores e rode-os AO MESMO TEMPO:
    #     resultados = await asyncio.gather(*(Runner.run(e, texto) for e in extratores))
    #   depois chame votar([r.final_output for r in resultados]) e devolva (pedido_final, divergencia, votos).
    #   Conceito: aula7/exemplos/08_paralelismo/main.py (fan-out/fan-in), aqui em asyncio, sem grafo.
    raise NotImplementedError("🆕 A.2: extrair_com_votacao")


def votar(votos: list[Pedido]) -> tuple[Pedido, bool]:
    # 🆕 A.3 -- decida por MAIORIA os campos tipo, matricula, data_inicio, data_fim e dias_vendidos
    #   (Counter(valores).most_common(1) ajuda). Os demais campos vêm do primeiro voto.
    #   Se NÃO houver maioria (2 de 3) em `tipo` ou em alguma das datas: divergencia=True
    #   (o sistema vai pedir esclarecimento em vez de adivinhar).
    #   Devolva (Pedido decidido, divergencia). Dica: votos[0].model_copy(update={...}).
    raise NotImplementedError("🆕 A.3: votar")


def _demo_extracao() -> None:
    for nome in ("C1_abono_simples", "C2_ferias_com_venda", "C5_sem_matricula", "C11_diaria_exterior"):
        pedido = extrair(CASOS[nome]["pedido"])
        print(f"\n{nome}\n  {pedido.model_dump()}")


def _demo_votacao() -> None:
    for nome in ("C1_abono_simples", "C2_ferias_com_venda", "C9_divergencia"):
        texto = CASOS[nome]["pedido"]
        inicio = time.perf_counter()
        pedido, divergencia, votos = asyncio.run(extrair_com_votacao(texto))
        segundos = time.perf_counter() - inicio
        print(f"\n{nome}  ({segundos:.1f}s, divergencia={divergencia})")
        for i, voto in enumerate(votos, 1):
            print(f"  voto {i}: tipo={voto.tipo.value} {voto.data_inicio}..{voto.data_fim} vende={voto.dias_vendidos}")
        print(f"  decisão: {pedido.model_dump()}")
    # 🆕 A.4 -- meça também os 3 extratores EM SEQUÊNCIA (um Runner.run_sync depois do outro) para o C2
    #   e imprima os dois tempos. O paralelo fica perto do tempo de UMA chamada?
    raise NotImplementedError("🆕 A.4: comparar tempo paralelo x sequencial")


if __name__ == "__main__":
    print(f"[modelo] {MODELO}")
    _demo_votacao() if "--votacao" in sys.argv else _demo_extracao()
