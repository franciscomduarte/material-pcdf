"""
Exercício 7b — Triagem CLIENTE (pede parecer e aguarda a resposta)
Publica um pedido no tópico do Jurídico e fica ouvindo o tópico de resposta.

Rode o serviço (ex07_juridico_servico.py) ANTES deste cliente.
"""
import os
import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/molina")


def on_message(client, userdata, msg):
    resposta = json.loads(msg.payload)
    print(f"\n>>> parecer recebido [{resposta.get('id')}]:\n{resposta.get('parecer')}")
    client.disconnect()  # encerra após receber (demo simples)


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)

    # 1) escuta a resposta ANTES de pedir (para não perder a mensagem)
    cli.subscribe(f"{PREFIXO}/juridico/resposta")

    # 2) publica o pedido
    pedido = {"id": 124, "tipo": "furto", "descricao": "furto a pedestre no Setor Comercial Sul"}
    cli.publish(f"{PREFIXO}/juridico/analisar", json.dumps(pedido))
    print("pedido enviado, aguardando parecer...")

    cli.loop_forever()