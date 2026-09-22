"""
Ex 7b (TODO) — Triagem cliente: pede parecer e aguarda a resposta.
"""
import os, json
import paho.mqtt.client as mqtt
from dotenv import load_dotenv

load_dotenv()
BROKER = os.getenv("MQTT_BROKER", "broker.emqx.io")
PORT = int(os.getenv("MQTT_PORT", "1883"))
PREFIXO = os.getenv("MQTT_PREFIXO", "pcdf/demo")

def on_message(client, userdata, msg):
    resposta = json.loads(msg.payload)
    print(f"\n>>> parecer [{resposta.get('id')}]:\n{resposta.get('parecer')}")
    client.disconnect()

if __name__ == "__main__":
    cli = mqtt.Client()
    cli.on_message = on_message
    cli.connect(BROKER, PORT)
    # TODO 1: assine {PREFIXO}/juridico/resposta ANTES de pedir
    ...
    pedido = {
        "id": 456,
        "tipo": "extorsão",
        "descricao": "ameaça de divulgação de fotos íntimas mediante pagamento, via redes sociais, Plano Piloto",
    }
    # TODO 2: publique o pedido em {PREFIXO}/juridico/analisar
    ...
    print("pedido enviado, aguardando parecer...")
    cli.loop_forever()