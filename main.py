import os
import requests
import time

TOKEN = os.environ.get("TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

CHECKLIST = """📋 *Checklist Trading — Swing*

Avant d'entrer en position, valide chaque point :

*📑 Respect du plan*
☐ Ce trade correspond à une setup définie dans mon plan
☐ Je respecte mes règles d'entrée sans exception
☐ Je ne suis pas en train de "chasser" un trade manqué
☐ Je ne trade pas par FOMO ou par ennui

*📊 Analyse technique*
☐ La tendance générale (HTF) est en accord avec mon trade
☐ Mon niveau d'entrée est clairement identifié
☐ J'ai validé la confluence sur au moins 2 timeframes
☐ Le volume confirme le mouvement
☐ Pas d'événement macro majeur imminent

*🛡️ Gestion du risque*
☐ Mon stop\-loss est à un niveau logique
☐ Je risque max 1\-2% de mon capital sur ce trade
☐ Mon ratio risque/rendement est d'au moins 2:1
☐ La taille de position est calculée en fonction du stop
☐ Pas de trades corrélés ouverts qui amplifient le risque

*🧠 État psychologique*
☐ Je suis calme et concentré
☐ Je ne suis pas en mode revenge trading
☐ Je ne suis pas en surconfiance après une série de gains
☐ J'accepte d'avance la possibilité de perdre
☐ Je peux laisser tourner le trade sans surveiller en permanence

✅ *Tous les critères cochés ? Tu peux entrer\.*
⚠️ *Un critère manquant ? Reconsidère le trade\.*"""

def send_message(chat_id, text):
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "MarkdownV2"
    })

def get_updates(offset=None):
    params = {"timeout": 30, "offset": offset}
    r = requests.get(f"{API}/getUpdates", params=params, timeout=35)
    return r.json().get("result", [])

def main():
    print("Bot démarré...")
    offset = None
    while True:
        updates = get_updates(offset)
        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            if chat_id:
                send_message(chat_id, CHECKLIST)
        time.sleep(1)

if __name__ == "__main__":
    main()
