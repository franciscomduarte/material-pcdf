"""
Exercício 9 (esteira, estágio 2/3) — Triagem
Consome a entrada, classifica com LLM e empurra para o Jurídico. Tópicos casados.
"""
import os
import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from agents import Agent, Runner
from provedor import configurar

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/molina")
configurar()

triagem = Agent(
    name="Triagem",
    instructions=(
        "Classifique a ocorrência. Responda em JSON com as chaves "
        '"tipo", "gravidade" e "crime" (true/false). Só o JSON.'
    ),
)

def on_message(client, userdata, msg):
    oc = json.loads(msg.payload)
    classificacao = Runner.run_sync(triagem, str(oc)).final_output
    print(f"[triagem] {oc.get('id')}: {classificacao}")
    client.publish(
        f"{PREFIXO}/pipeline/juridico",
        json.dumps({"id": oc.get("id"), "classificacao": classificacao, "ocorrencia": oc}),
    )


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/pipeline/entrada")
    print("Esteira: Triagem ouvindo entrada... (Ctrl+C para sair)")
    cli.loop_forever()