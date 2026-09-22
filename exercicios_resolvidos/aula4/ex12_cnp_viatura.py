"""
Ex 12a (TODO) — Viatura (participante do Contract Net Protocol).
Cenário novo: em vez de delegacias disputando por carga de trabalho, viaturas
disputam por DISTÂNCIA até a ocorrência (menor distância vence).

Rode uma instância por viatura, cada uma com um nome:
  python todo/ex12_cnp_viatura.py VTR-01
  python todo/ex12_cnp_viatura.py VTR-02
Depois publique um cfp com: python todo/ex12_cnp_coordenador.py
"""
import os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")
NOME = sys.argv[1] if len(sys.argv) > 1 else "VTR-01"


def on_message(client, userdata, msg):
    m = json.loads(msg.payload)
    perf = m.get("performative")

    if perf == "cfp":
        distancia_km = round(random.uniform(0.5, 15), 1)
        # TODO 1: monte uma msg "propose" (performative, sender=NOME,
        #         receiver="coordenador", content={"distancia_km": distancia_km},
        #         in_reply_to=m.get("reply_with")) e publique em
        #         {PREFIXO}/cnp/propostas
        ...
        print(f"[{NOME}] cfp recebido -> propus distancia_km={distancia_km}")

    elif perf == "accept-proposal" and m.get("receiver") == NOME:
        print(f"[{NOME}] proposta ACEITA -> deslocando para {m.get('in_reply_to')}")
    elif perf == "reject-proposal" and m.get("receiver") == NOME:
        print(f"[{NOME}] proposta recusada para {m.get('in_reply_to')}")


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO 2: assine {PREFIXO}/cnp/cfp  e  {PREFIXO}/cnp/decisao/{NOME}
    ...
    print(f"Viatura {NOME} ouvindo... (Ctrl+C para sair)")
    cli.loop_forever()
