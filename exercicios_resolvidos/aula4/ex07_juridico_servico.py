"""
Ex 7a (TODO) — Jurídico como serviço assíncrono (Request/Reply).
pedido -> {PREFIXO}/juridico/analisar ; resposta -> {PREFIXO}/juridico/resposta
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from agents import Agent, Runner
from provedor import configurar

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")
configurar()

juridico = Agent(name="Jurídico", instructions="Enquadramento legal provável, 2 linhas.")

def on_message(client, userdata, msg):
    pedido = json.loads(msg.payload)
    # TODO 1: gere o parecer com Runner.run_sync(juridico, ...)
    parecer = ...
    # TODO 2: publique {"id":..., "parecer":...} em {PREFIXO}/juridico/resposta
    ...

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO 3: assine {PREFIXO}/juridico/analisar e ouça
    ...