"""
Exercício 4 — Coletor (publisher MQTT)
Publica uma ocorrência num tópico e SEGUE (assíncrono). Não conhece quem consome.

Rode (com um assinante já ouvindo): python ex04_mqtt_pub.py
"""
import os
import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/molina")

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.connect(BROKER, PORT)

    ocorrencia = {"id": 123, "tipo": "estupro", "local": "Asa Norte"}
    cli.publish(f"{PREFIXO}/ocorrencias/nova", json.dumps(ocorrencia))
    print("ocorrência publicada:", ocorrencia)

    cli.disconnect()
