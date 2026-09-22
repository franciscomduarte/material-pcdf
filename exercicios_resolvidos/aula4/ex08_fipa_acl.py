"""
Ex 8 (TODO) — Mensagem FIPA-ACL (publisher). Publica em {PREFIXO}/acl/...
"""
import os, json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

def msg_acl(performativa, sender, receiver, content, **extra):
    # TODO 1: monte e devolva um dict com os campos:
    #   performative, sender, receiver, content,
    #   ontology="seguranca-publica", language="pt-BR",
    #   mais os campos que vierem em **extra
    ...

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.connect(BROKER, PORT)
    # TODO 2: monte uma msg "request" (coletor pede à triagem que verifique o
    #         veículo "veiculo-789") e publique em {PREFIXO}/acl/triagem
    ...
    # TODO 3: monte uma msg "inform" (triagem informa ao coletor que o veículo
    #         "veiculo-789" está "suspeito, gravidade media") e publique em
    #         {PREFIXO}/acl/coletor
    ...
    cli.disconnect()