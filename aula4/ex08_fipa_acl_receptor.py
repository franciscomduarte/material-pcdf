"""
Exercício 8 (receptor) — lê mensagens FIPA-ACL e age pela PERFORMATIVA
Assina {PREFIXO}/acl/# e decide o que fazer a partir da intenção da mensagem
(request, inform, ...). Plug-and-play com ex08_fipa_acl.py (mesmos tópicos).

Rode este receptor PRIMEIRO, depois publique com: python ex08_fipa_acl.py
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
    m = json.loads(msg.payload)
    perf = m.get("performative")
    # o receptor decide a ação pela intenção (performativa), não pelo texto
    if perf == "request":
        print(f"[request] {m['sender']} pediu: {m['content']} -> vou processar")
    elif perf == "inform":
        print(f"[inform]  {m['sender']} informou: {m['content']} -> vou registrar")
    else:
        print(f"[{perf}] {m.get('content')}")


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/acl/#")
    print("Receptor ACL ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()
