"""
Ex 9 (TODO, estágio 1/3) — Coletor da esteira. Publica em {PREFIXO}/pipeline/entrada
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
    ocorrencias = [
        {"id": 10, "descricao": "Invasão de domicílio com subtração de bens eletrônicos, Sobradinho"},
        {"id": 11, "descricao": "Perda de documento pessoal (RG) comunicada para fins de registro, sem indício de crime"},
    ]
    # TODO: publique cada ocorrência em {PREFIXO}/pipeline/entrada
    ...
    cli.disconnect()