"""
Ex 6 (TODO) — Estatística de placas (terceiro assinante, contador).

Cenário novo: conta quantas placas foram lidas por local, sem tocar no
scanner (Ex 4) nem no Verificador (Ex 5) — mesmo desafio de fan-out visto em
aula, com um agregado diferente (por local, não por tipo).

Rode junto com o Ex 5 e publique com o Ex 4.
"""
import os, json
from collections import Counter
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/molina")

contagem = Counter()

def on_message(client, userdata, msg):
    leitura = json.loads(msg.payload)

    #RESPOSTA
    contagem[leitura.get("local", "desconhecido")] += 1
    print("Leituras por local:", dict(contagem))

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)

    #RESPOSTA
    cli.subscribe(f"{PREFIXO}/placas/#")
    cli.loop_forever()