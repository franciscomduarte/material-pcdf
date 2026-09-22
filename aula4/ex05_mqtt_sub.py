"""
Exercício 5 — Triagem (subscriber MQTT com LLM)
Assina o tópico de ocorrências e classifica cada uma que chega.

Rode (deixe ouvindo): python ex05_mqtt_sub.py
Depois publique com o ex04 noutro terminal.
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
    instructions="Classifique a ocorrência recebida (tipo e gravidade) em uma linha.",
)

def on_message(client, userdata, msg):
    oc = json.loads(msg.payload)
    resultado = Runner.run_sync(triagem, str(oc))
    print(f"[{oc.get('id')}] {resultado.final_output}")


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/ocorrencias/#")
    print("Triagem ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()