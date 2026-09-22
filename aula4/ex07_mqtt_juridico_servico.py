"""
Exercício 7a — Jurídico como SERVIÇO assíncrono (Request/Reply via MQTT)
Assina o tópico de pedidos, analisa com LLM e PUBLICA a resposta noutro tópico.

Padrão Request/Reply sobre mensageria:
  pedido   -> {PREFIXO}/juridico/analisar   (quem pede publica aqui)
  resposta -> {PREFIXO}/juridico/resposta   (o serviço responde aqui)

Rode primeiro este serviço, depois o cliente (ex07_triagem_cliente.py).
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
    instructions="Avalie o enquadramento legal da ocorrência e cite o artigo provável, em 2 linhas.",
)

def on_message(client, userdata, msg):
    pedido = json.loads(msg.payload)
    print("pedido recebido:", pedido)
    parecer = Runner.run_sync(juridico, str(pedido)).final_output
    resposta = {"id": pedido.get("id"), "parecer": parecer}
    client.publish(f"{PREFIXO}/juridico/resposta", json.dumps(resposta))
    print("resposta publicada.")


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/juridico/analisar")
    print("Serviço Jurídico no ar... (Ctrl+C para sair)")
    cli.loop_forever()
