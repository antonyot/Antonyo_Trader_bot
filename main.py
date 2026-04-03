import os
import json
import time
import urllib.request
import urllib.parse

TOKEN = os.environ.get("TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"

CHECKLIST_ITEMS = [
    "Setup definie dans mon plan",
    "Regles d'entree respectees",
    "Pas de trade manque a rattraper",
    "Pas de FOMO ou ennui",
    "Tendance HTF en accord",
    "Niveau d'entree identifie",
    "Confluence sur 2 timeframes",
    "Volume confirme",
    "Pas de news majeure imminente",
    "Stop-loss a un niveau logique",
    "Risque max 1-2% du capital",
    "Ratio R/R minimum 2:1",
    "Taille de position calculee",
    "Pas de trades correles ouverts",
    "Calme et concentre",
    "Pas de revenge trading",
    "Pas de surconfiance",
    "Perte acceptee d'avance",
    "Pas besoin de surveiller en permanence"
]

sessions = {}
historique = []

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

def envoyer_checklist(chat_id):
    sessions[chat_id] = {"reponses": [], "index": 0}
    item = CHECKLIST_ITEMS[0]
    send_message(chat_id, f"CHECKLIST TRADING - Question 1/{len(CHECKLIST_ITEMS)}\n\n{item}\n\nReponds par oui ou non")

def question_suivante(chat_id, reponse):
    session = sessions[chat_id]
    session["reponses"].append(reponse)
    session["index"] += 1

    if session["index"] < len(CHECKLIST_ITEMS):
        i = session["index"]
        item = CHECKLIST_ITEMS[i]
        send_message(chat_id, f"Question {i+1}/{len(CHECKLIST_ITEMS)}\n\n{item}\n\nReponds par oui ou non")
    else:
        terminer_session(chat_id)

def terminer_session(chat_id):
    session = sessions[chat_id]
    reponses = session["reponses"]
    oui = sum(1 for r in reponses if r == "oui")
    total = len(reponses)
    pct = round(oui / total * 100)

    date = time.strftime("%d/%m/%Y %H:%M")
    historique.append({"date": date, "oui": oui, "total": total, "pct": pct})

    details = ""
    for i, item in enumerate(CHECKLIST_ITEMS):
        emoji = "OK" if reponses[i] == "oui" else "X"
        details += f"{emoji} {item}\n"

    msg = f"RESULTAT DE LA SESSION\n{date}\n\n{details}\nScore : {oui}/{total} ({pct}%)\n"
    if pct == 100:
        msg += "\nTout coche - tu peux entrer"
    elif pct >= 75:
        msg += "\nMajoritairement valide - attention aux points manquants"
    else:
        msg += "\nTrop de criteres manquants - ne prends pas ce trade"

    send_message(chat_id, msg)
    del sessions[chat_id]

def envoyer_historique(chat_id):
    if not historique:
        send_message(chat_id, "Pas encore d'historique. Lance une checklist avec 'checklist'")
        return

    msg = "HISTORIQUE DES SESSIONS\n\n"
    for h in historique[-10:]:
        msg += f"{h['date']} - {h['oui']}/{h['total']} ({h['pct']}%)\n"

    total_sessions = len(historique)
    moyenne = round(sum(h['pct'] for h in historique) / total_sessions)
    msg += f"\nTotal sessions : {total_sessions}"
    msg += f"\nScore moyen : {moyenne}%"
    send_message(chat_id, msg)

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
                text = message.get("text", "").lower().strip()

                if not chat_id or not text:
                    continue

                if text in ["checklist", "start", "/checklist", "/start"]:
                    envoyer_checklist(chat_id)
                elif text == "historique" or text == "/historique":
                    envoyer_historique(chat_id)
                elif chat_id in sessions:
                    if text in ["oui", "non"]:
                        question_suivante(chat_id, text)
                    else:
                        send_message(chat_id, "Reponds uniquement par oui ou non")
                else:
                    send_message(chat_id, "Tape 'checklist' pour lancer la checklist\nTape 'historique' pour voir tes sessions passees")

        except Exception as e:
            print(f"Erreur: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
