"""
Exemplo 02 -- AGENTES ESPECIALIZADOS.

No exemplo 01 um agente fazia tudo. Agora dividimos por PAPÉIS:

    SOLICITAÇÃO -> INVESTIGADOR -> JURÍDICO -> ANALISTA

Cada especialista tem OBJETIVO, INSTRUÇÕES, ENTRADA e SAÍDA bem definidos.

Atenção: especializar NÃO exige modelos diferentes. Os três usam o MESMO LLM.
O que os diferencia é:  prompt (instruções) . responsabilidade . contexto de
entrada . critério de saída  (e, em sistemas reais, ferramentas -- veja o exemplo 05).

Repare no incômodo deste exemplo: quem leva o resultado de um especialista ao
próximo somos NÓS, à mão, passando strings de uma chamada para outra. Com três
especialistas é tolerável; com dez, vira bagunça. O exemplo 03 resolve isso com
um ESTADO COMPARTILHADO.

Rodar (LLM REAL: configure o .env; veja o README), a partir de aula7/:
    python exemplos\\02_agentes_especializados\\main.py
"""
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import prompts
from caso import DENUNCIA_045
from provedor import obter_modelo

modelo = obter_modelo()  # LLM REAL: PROVEDOR no .env (openai ou ollama)

SOLICITACAO = DENUNCIA_045


@dataclass
class Especialista:
    nome: str
    objetivo: str
    instrucoes: str
    entrada: str       # o que ele recebe (descrição)
    saida: str         # o que ele entrega (descrição)

    def executar(self, contexto: str) -> str:
        print(f"[{self.nome.upper()}] {self.objetivo}")
        return modelo.gerar(
            f"Você é o {self.nome} de um órgão de controle. Objetivo: {self.objetivo}\n"
            f"Instruções: {self.instrucoes} Responda em no máximo 3 frases.\n"
            f"{prompts.REGRA}\n"
            f"Entrada ({self.entrada}):\n{contexto}"
        )


investigador = Especialista(
    nome="Investigador",
    objetivo="levantar os fatos da contratação",
    instrucoes="Liste apenas fatos verificáveis. Não opine e não cite leis.",
    entrada="a denúncia",
    saida="fatos levantados",
)
juridico = Especialista(
    nome="Jurídico",
    objetivo="enquadrar os fatos na legislação",
    instrucoes="Aponte normas potencialmente violadas. Não avalie risco e não recomende ações.",
    entrada="os fatos levantados",
    saida="enquadramento legal",
)
analista = Especialista(
    nome="Analista",
    objetivo="avaliar o risco a partir dos fatos e do enquadramento",
    instrucoes="Classifique o risco em BAIXO, MÉDIO ou ALTO e justifique em uma frase.",
    entrada="fatos + enquadramento",
    saida="avaliação de risco",
)

if __name__ == "__main__":
    print(f"Modelo em uso: {modelo.nome}\n")

    # Passamos o resultado de um para o outro NA MÃO.
    fatos = investigador.executar(SOLICITACAO)
    print("  ->", fatos, "\n")

    enquadramento = juridico.executar(fatos)
    print("  ->", enquadramento, "\n")

    risco = analista.executar(f"Fatos: {fatos}\nEnquadramento: {enquadramento}")
    print("  ->", risco, "\n")

    print("Cada especialista faz UMA coisa. Mas o encadeamento está nas variáveis soltas do script:")
    print("o fluxo e os dados ainda não são explícitos. Próximo exemplo: estado compartilhado.")
