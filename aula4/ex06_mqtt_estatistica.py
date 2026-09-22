"""
Exercício 6 — Estatística (terceiro assinante, fan-out do Pub/Sub)
Assina o MESMO tópico da Triagem e apenas conta ocorrências por tipo.
Mostra que adicionar um consumidor NÃO muda o Coletor.

Rode junto com o ex05 e publique com o ex04.
"""
import os
import json
from collections import Counter

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/molina")
contagem = Counter()


def on_message(client, userdata, msg):
    oc = json.loads(msg.payload)
    contagem[oc.get("tipo", "desconhecido")] += 1
    print("Ocorrências por tipo:", dict(contagem))


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/ocorrencias/#")
    print("Estatística ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()
