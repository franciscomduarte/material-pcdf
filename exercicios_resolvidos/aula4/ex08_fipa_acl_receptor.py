"""
Ex 8 (TODO, receptor) — age pela PERFORMATIVA. Assina {PREFIXO}/acl/#
"""
import os, json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

def on_message(client, userdata, msg):
    m = json.loads(msg.payload)
    perf = m.get("performative")
    # TODO: trate 'request' e 'inform' de formas diferentes (imprima a ação por intenção)
    ...

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO: assine {PREFIXO}/acl/# e ouça
    ...
