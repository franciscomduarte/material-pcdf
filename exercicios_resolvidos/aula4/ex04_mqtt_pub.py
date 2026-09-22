"""
Ex 4 (TODO) — Scanner de placas (publisher MQTT).

Cenário novo (diferente do Coletor de ocorrências visto em aula): este é um
scanner de leitura automática de placas (ANPR) que publica cada leitura que
faz. Mesmo mecanismo do Coletor — publica e segue, sem saber quem consome.

Rode (com um assinante já ouvindo): python todo/ex04_mqtt_pub.py
"""
import os, json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.connect(BROKER, PORT)
    leitura = {"placa": "ABC1D23", "local": "Praça do Relógio", "sentido": "norte"}
    # TODO: publique a leitura (json.dumps) no tópico {PREFIXO}/placas/lida
    ...
    cli.disconnect()