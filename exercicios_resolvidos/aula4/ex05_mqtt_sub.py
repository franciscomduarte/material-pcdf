"""
Ex 5 (TODO) — Verificador de placas (subscriber MQTT com LLM).

Cenário novo: assina as leituras do scanner (Ex 4) e avalia, em uma linha, se
a leitura merece atenção ou é rotina. Sem base de dados real — o LLM só
simula o parecer a partir do texto da leitura (ex.: sentido, horário, local).

Rode (deixe ouvindo): python todo/ex05_mqtt_sub.py
Depois publique com o Ex 4 noutro terminal.
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

verificador = Agent(
    name="Verificador",
    instructions="Avalie a leitura de placa recebida em uma linha: 'atenção' ou 'rotina', com um motivo breve.",
)

def on_message(client, userdata, msg):
    leitura = json.loads(msg.payload)
    # TODO: rode o Verificador sobre a leitura e imprima o resultado
    ...

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO: assine {PREFIXO}/placas/#  e chame cli.loop_forever()
    ...