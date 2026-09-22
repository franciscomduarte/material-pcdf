"""
Ex 13a (TODO) — Enriquecimento (novo assinante da esteira do Ex 9, fan-out).
Assina pipeline/entrada (o MESMO tópico da Triagem) e publica região +
prioridade em pipeline/enriquecimento. Nenhum arquivo do Ex 9 muda.
Rode junto com os estágios do Ex 9: python todo/ex13_pipeline_enriquecimento.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from agents import Agent, Runner
from provedor import configurar

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")
configurar()

enriquecimento = Agent(
    name="Enriquecimento",
    instructions=(
        'Responda em JSON com "regiao" (ou "indefinida") e '
        '"prioridade" ("alta", "media" ou "baixa"). Só o JSON.'
    ),
)


def on_message(client, userdata, msg):
    oc = json.loads(msg.payload)
    # TODO 1: rode o Enriquecimento sobre `oc` (str(oc) como entrada)
    dados = ...
    print(f"[enriquecimento] {oc.get('id')}: {dados}")
    # TODO 2: publique {"id": oc.get("id"), "enriquecimento": dados}
    #         em {PREFIXO}/pipeline/enriquecimento
    ...


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO 3: assine {PREFIXO}/pipeline/entrada e ouça
    ...
