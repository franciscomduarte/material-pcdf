"""
Exercício 8 — Mensagem no estilo FIPA-ACL sobre MQTT
Toda mensagem entre agentes carrega uma INTENÇÃO (performativa), não só texto.
Aqui montamos uma mensagem ACL (request/inform) e a enviamos via MQTT; o
receptor decide o que fazer a partir da performativa.

Rode: python ex08_fipa_acl.py   (publica) — deixe um assinante ouvindo o
tópico {PREFIXO}/acl/# para ver as mensagens chegando (ex05 adaptado, se quiser).
"""
import os
import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/molina")


def msg_acl(performativa, sender, receiver, content, **extra):
    """Monta uma mensagem no formato FIPA-ACL (como dict serializável)."""
    base = {
        "performative": performativa,   # request, inform, query, agree, refuse...
        "sender": sender,
        "receiver": receiver,
        "content": content,
        "ontology": "seguranca-publica",
        "language": "pt-BR",
    }
    base.update(extra)
    return base


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.connect(BROKER, PORT)

    # pedido: Coletor pede à Triagem que classifique
    req = msg_acl("request", "coletor", "triagem",
                  "classificar(ocorrencia-123)", reply_with="ocorrencia-123")
    cli.publish(f"{PREFIXO}/acl/triagem", json.dumps(req))

    # informe: Triagem informa a classificação de volta
    inform = msg_acl("inform", "triagem", "coletor",
                     "classificacao(ocorrencia-123, furto, baixa)",
                     in_reply_to="ocorrencia-123")
    cli.publish(f"{PREFIXO}/acl/coletor", json.dumps(inform))

    print("mensagens ACL publicadas:")
    print("  ->", req["performative"], req["content"])
    print("  ->", inform["performative"], inform["content"])
    cli.disconnect()

    