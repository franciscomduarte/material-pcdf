"""
ModeloMock do exemplo 11 -- LLM de mentira, determinístico, sem internet e sem API Key.

Lê a linha "TAREFA: ..." do prompt:

  - extrair : acha região e datas (AAAA-MM-DD) na solicitação e devolve JSON;
              o que não achar vai como null
  - redigir : havendo eventos, na 1ª tentativa devolve um resumo VAGO (sem citá-los);
              com "Correção solicitada" (ciclo de revisão) devolve o texto completo
  - validar : reprova se algum evento do bloco FATOS não aparece na resposta
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from provedor import Modelo


def _linha(prompt: str, rotulo: str) -> str:
    achou = re.search(rf"^{rotulo}: (.*)$", prompt, re.MULTILINE)
    return achou.group(1).strip() if achou else ""


class ModeloMock(Modelo):
    nome = "mock"

    def gerar(self, prompt: str) -> str:
        if "TAREFA: extrair" in prompt:
            texto = prompt.split("Solicitação:", 1)[1]
            regiao = re.search(r"\b(Alfa|Bravo|Charlie|Foxtrot|Golf|Kilo)\b", texto)
            datas = re.findall(r"\d{4}-\d{2}-\d{2}", texto)
            return json.dumps(
                {
                    "regiao": regiao.group(1) if regiao else None,
                    "data_inicio": datas[0] if datas else None,
                    "data_fim": datas[-1] if datas else None,
                }
            )

        if "TAREFA: redigir" in prompt:
            if "Correção solicitada" not in prompt and _linha(prompt, "Eventos") != "nenhum":
                return "Há movimentação prevista no período. Recomenda-se atenção redobrada."
            partes = [f"Região {_linha(prompt, 'Região')}, {_linha(prompt, 'Período')}."]
            if _linha(prompt, "Eventos") != "nenhum":
                partes.append(f"Eventos: {_linha(prompt, 'Eventos')}.")
            if _linha(prompt, "Feriados") != "nenhum":
                partes.append(f"Feriados: {_linha(prompt, 'Feriados')}.")
            partes.append(f"Risco {_linha(prompt, 'Risco')}.")
            if _linha(prompt, "Efetivo") != "não necessário":
                partes.append(f"Efetivo recomendado: {_linha(prompt, 'Efetivo')}.")
            return " ".join(partes)

        if "TAREFA: validar" in prompt:
            eventos = _linha(prompt, "Eventos")
            resposta = prompt.split("Resposta:", 1)[1]
            faltando = [e for e in eventos.split("; ") if e != "nenhum" and e not in resposta]
            return f"ERRO: a resposta não cita o evento '{faltando[0]}'" if faltando else "OK"

        return "Resposta simulada pelo modelo."
