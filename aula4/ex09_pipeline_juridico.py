"""
Exercício 9 (esteira, estágio 3/3) — Jurídico
Consome o que a Triagem empurrou e emite o parecer final. Tópicos casados.
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

juridico = Agent(
    name="Juridico",
    instructions="Com base na classificação, dê o enquadramento legal provável em 2 linhas.",
)


def on_message(client, userdata, msg):
    item = json.loads(msg.payload)
    parecer = Runner.run_sync(juridico, str(item)).final_output
    print(f"[juridico] {item.get('id')}: {parecer}")


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/pipeline/juridico")
    print("Esteira: Jurídico ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()
