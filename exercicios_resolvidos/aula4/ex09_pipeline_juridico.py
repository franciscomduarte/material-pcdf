"""
Ex 9 (TODO, estágio 3/3) — Jurídico. Consome de {PREFIXO}/pipeline/juridico
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
    item = json.loads(msg.payload)
    # TODO: gere o parecer final e imprima
    ...

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO: assine {PREFIXO}/pipeline/juridico e ouça
    ...