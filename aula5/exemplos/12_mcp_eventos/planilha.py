"""
planilha.py -- acesso à planilha de eventos (Google Sheets publicada como CSV).

Mesmo papel do database.py nos outros exemplos: este módulo é o ÚNICO lugar
que sabe de onde vêm os eventos. O server.py, o agente e o LLM só veem a tool.

Fonte, por ordem:
  1. EVENTOS_CSV_URL (no .env): link "Publicar na Web -> CSV" do Google Sheets.
  2. dados/eventos.csv: cópia local, usada se a URL não estiver configurada ou
     se a planilha estiver fora do ar (sem internet na sala, por exemplo).
"""
import csv
import io
import os
import re
import sys
import time
import urllib.request
from datetime import date, datetime
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parents[2]  # aula5/
load_dotenv(RAIZ / ".env")

CSV_LOCAL = RAIZ / "dados" / "eventos.csv"
CACHE_SEGUNDOS = 60

_cache: dict = {"quando": 0.0, "linhas": [], "fonte": ""}


def _preparar_url(url: str) -> str:
    """Converte links de compartilhamento do Google em links que devolvem o CSV.

    - Arquivo do Drive  (drive.google.com/file/d/ID/view)  -> download direto
    - Planilha aberta   (docs.google.com/spreadsheets/d/ID/edit) -> exportação em CSV
    Links "Publicar na Web" (.../d/e/.../pub?output=csv) já servem e ficam como estão.
    """
    m = re.search(r"drive\.google\.com/file/d/([\w-]+)", url)
    if m:
        return f"https://drive.google.com/uc?export=download&id={m.group(1)}"
    m = re.search(r"docs\.google\.com/spreadsheets/d/(?!e/)([\w-]+)", url)
    if m:
        return f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=csv"
    return url


def _parece_csv_de_eventos(texto: str) -> bool:
    """A primeira linha precisa ser o cabeçalho (data, regiao...). Uma página HTML não é."""
    primeira = next((l for l in texto.splitlines() if l.strip()), "").lower()
    return not primeira.lstrip().startswith("<") and "data" in primeira and "regiao" in primeira


def _ler_texto() -> tuple[str, str]:
    """Devolve (conteúdo do CSV, descrição da fonte)."""
    url = os.getenv("EVENTOS_CSV_URL", "").strip()
    if url:
        try:
            with urllib.request.urlopen(_preparar_url(url), timeout=10) as resposta:
                texto = resposta.read().decode("utf-8-sig")
            if _parece_csv_de_eventos(texto):
                return texto, "planilha publicada"
            print("[planilha] a URL não devolveu um CSV de eventos (parece uma página HTML: "
                  "o link precisa dar acesso público ao arquivo); usando o CSV local", file=sys.stderr)
        except Exception as erro:  # rede fora, link errado, planilha despublicada...
            print(f"[planilha] não consegui ler a URL ({erro}); usando o CSV local", file=sys.stderr)
    return CSV_LOCAL.read_text(encoding="utf-8-sig"), "CSV local"


def _ler_data(texto: str) -> date | None:
    """Aceita AAAA-MM-DD e DD/MM/AAAA (planilhas em português costumam exibir as datas assim)."""
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def _normalizar(linha: dict) -> dict | None:
    """Limpa uma linha da planilha. Planilhas são editadas à mão: não confie no formato."""
    data = _ler_data((linha.get("data") or "").strip())
    if data is None:
        return None  # linha sem data válida: ignora
    publico = (linha.get("publico_estimado") or "").strip().replace(".", "")
    return {
        "data": data.isoformat(),
        "regiao": " ".join((linha.get("regiao") or "").split()),
        "tipo_evento": (linha.get("tipo_evento") or "").strip().upper(),
        "nome": (linha.get("nome") or "").strip(),
        "publico_estimado": int(publico) if publico.isdigit() else None,
    }


def carregar_eventos() -> tuple[list[dict], str]:
    """Lê a planilha (com cache curto) e devolve (eventos, fonte)."""
    agora = time.time()
    if _cache["linhas"] and agora - _cache["quando"] < CACHE_SEGUNDOS:
        return _cache["linhas"], _cache["fonte"]

    texto, fonte = _ler_texto()
    leitor = csv.DictReader(io.StringIO(texto))
    linhas = [n for n in (_normalizar(l) for l in leitor) if n]
    _cache.update(quando=agora, linhas=linhas, fonte=fonte)
    return linhas, fonte
