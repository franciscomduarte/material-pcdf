"""
Ex 13b (TODO) — Agregador (fan-in: junta pipeline/juridico + pipeline/enriquecimento pelo id).
Só publica o dossiê quando as DUAS partes daquele id já chegaram.
Rode junto com os demais estágios: python todo/ex13_pipeline_agregador.py
"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

pendentes = {}


def on_message(client, userdata, msg):
    m = json.loads(msg.payload)
    id_ = m.get("id")
    parcial = pendentes.setdefault(id_, {})

    # TODO 1: se msg.topic terminar em "/pipeline/juridico", guarde
    #         parcial["classificacao"] = m.get("classificacao");
    #         se terminar em "/pipeline/enriquecimento", guarde
    #         parcial["enriquecimento"] = m.get("enriquecimento")
    ...

    if "classificacao" in parcial and "enriquecimento" in parcial:
        dossie = {"id": id_, **parcial}
        print(f"[agregador] dossiê consolidado -> {dossie}")
        # TODO 2: publique `dossie` em {PREFIXO}/pipeline/dossie e remova o
        #         id de `pendentes`
        ...


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO 3: assine {PREFIXO}/pipeline/juridico e {PREFIXO}/pipeline/enriquecimento
    ...
    print("Esteira: Agregador ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()
