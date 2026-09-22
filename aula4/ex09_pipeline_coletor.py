"""
Exercício 9 (esteira, estágio 1/3) — Coletor
Publica ocorrências cruas na entrada da esteira. Plug-and-play: tópicos já casados.

Ordem de execução (3 terminais):
  1) python ex09_pipeline_juridico.py     (estágio final)
  2) python ex09_pipeline_triagem.py      (estágio do meio)
  3) python ex09_pipeline_coletor.py      (dispara a esteira)
"""
import os
import json

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/molina")

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.connect(BROKER, PORT)
    for oc in [
        {"id": 1, "descricao": "Roubo a pedestre no Setor Comercial Sul"},
        {"id": 2, "descricao": "Bicicleta encontrada e devolvida no Parque da Cidade"},
    ]:
        cli.publish(f"{PREFIXO}/pipeline/entrada", json.dumps(oc))
        print("entrada publicada:", oc)
    cli.disconnect()
