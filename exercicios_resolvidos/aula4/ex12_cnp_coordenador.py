"""
Ex 12b (TODO) — Coordenador do Contract Net Protocol (CNP).
Publica um cfp, aguarda propostas das viaturas e aceita a de MENOR distância.
Rode as viaturas ANTES (todo/ex12_cnp_viatura.py), depois:
  python todo/ex12_cnp_coordenador.py
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")
JANELA_PROPOSTAS = float(os.getenv("CNP_JANELA_S", "4"))
propostas = []


def on_message(client, userdata, msg):
    m = json.loads(msg.payload)
    if m.get("performative") == "propose":
        propostas.append(m)
        print(f"[coordenador] proposta de {m['sender']}: {m['content']}")


if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    cli.subscribe(f"{PREFIXO}/cnp/propostas")
    cli.loop_start()

    ocorrencia_id = "ocorrencia-88"
    cfp = {
        "performative": "cfp", "sender": "coordenador", "receiver": "todas-viaturas",
        "content": "Perturbação do sossego no Sudoeste — quem atende?",
        "reply_with": ocorrencia_id,
    }
    cli.publish(f"{PREFIXO}/cnp/cfp", json.dumps(cfp))
    print(f"[coordenador] cfp publicado, aguardando propostas por {JANELA_PROPOSTAS:.0f}s...")
    time.sleep(JANELA_PROPOSTAS)
    cli.loop_stop()

    if not propostas:
        print("[coordenador] nenhuma proposta recebida — as viaturas estão ouvindo?")
    else:
        # TODO 1: ache a proposta vencedora = menor content["distancia_km"]
        vencedora = ...
        print(f"\n[coordenador] vencedora: {vencedora['sender']}")
        for p in propostas:
            # TODO 2: monte "accept-proposal" para a vencedora e
            #         "reject-proposal" para as demais, e publique cada uma em
            #         {PREFIXO}/cnp/decisao/{p['sender']}
            ...

    cli.disconnect()
