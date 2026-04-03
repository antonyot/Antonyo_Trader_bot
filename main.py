import os
import json
import time
import urllib.request
import urllib.parse

TOKEN = os.environ.get("TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

CHECKLIST = """Checklist Trading - Swing

Avant d'entrer en position, valide chaque point :

RESPECT DU PLAN
- Ce trade correspond a une setup definie dans mon plan
- Je respecte mes regles d'entree sans exception
- Je ne suis pas en train de chasser un trade manque
- Je ne trade pas par FOMO ou par ennui

ANALYSE TECHNIQUE
- La tendance generale (HTF) est en accord avec mon trade
- Mon niveau d'entree est clairement identifie
- J'ai valide la confluence sur au moins 2 timeframes
- Le volume confirme le mouvement
- Pas d'evenement macro majeur imminent

GESTION DU RISQUE
- Mon stop-loss est a un niveau logique
- Je risque max 1-2% de mon capital sur ce trade
- Mon ratio risque/rendement est d'au moins 2:1
- La taille de position est calculee en fonction du stop
- Pas de trades correles ouverts qui amplifient le risque

ETAT PSYCHOLOGIQUE
- Je suis calme et concentre
- Je ne suis pas en mode revenge trading
- Je ne suis pas en surconfiance apres une serie de gains
- J'accepte d'avance la possibilite de perdre
- Je peux laisser tourner le trade sans surveiller en permanence

Tous les criteres coches ? Tu peux entrer.
Un critere manquant ? Reconsidere le trade."""

def send_message(chat_id, text):
    data = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(f"{API}/sendMessage", data=data, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

def get_updates(offset=None):
    url = f"{API}/getUpdates?timeout=30"
    if offset:
        url += f"&offset={offset}"
    with urllib.request.urlopen(url, timeout=35) as r:
        return json.loads(r.read()).get("result", [])

def main():
    print("Bot demarre...")
    offset = None
    while True:
        try:
            updates = get_updates(offset)
            for update in updates:
                offset = update["update_id"] + 1
                message = update.get("message", {})
                chat_id = message.get("chat", {}).get("id")
                if chat_id:
                    send_message(chat_id, CHECKLIST)
        except Exception as e:
            print(f"Erreur: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
