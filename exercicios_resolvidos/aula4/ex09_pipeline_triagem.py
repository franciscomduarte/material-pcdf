"""
Ex 9 (TODO, estágio 2/3) — Triagem. entrada -> classifica -> empurra p/ juridico
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

triagem = Agent(name="Triagem", instructions='Classifique em JSON: "tipo","gravidade","crime". Só o JSON.')

def on_message(client, userdata, msg):
    oc = json.loads(msg.payload)
    # TODO 1: classifique com a Triagem
    classificacao = ...
    # TODO 2: publique {"id":..., "classificacao":..., "ocorrencia":oc} em {PREFIXO}/pipeline/juridico
    ...

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO 3: assine {PREFIXO}/pipeline/entrada e ouça
    ...