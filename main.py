import os
import json
import time
import urllib.request
import urllib.parse

TOKEN = os.environ.get("TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"
SHEETS_URL = "https://script.google.com/macros/s/AKfycbxq3dgto7MHKgijoF1rQP35cbXE0EitKORqfzfMK04sBrurw9lSNOQvFpKuAwK8GDYl/exec"

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

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

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

def envoyer_vers_sheets(payload):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(SHEETS_URL, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Erreur Sheets: {e}")

def envoyer_checklist(chat_id):
    sessions[chat_id] = {
        "etape": "checklist",
        "reponses": [],
        "index": 0,
        "timestamp": time.time()
    }
    item = CHECKLIST_ITEMS[0]
    send_message(chat_id, f"CHECKLIST TRADING\nQuestion 1/{len(CHECKLIST_ITEMS)}\n\n{item}\n\nReponds par oui ou non")

def question_suivante(chat_id, reponse):
    session = sessions[chat_id]
    session["reponses"].append(reponse)
    session["index"] += 1

    if session["index"] < len(CHECKLIST_ITEMS):
        i = session["index"]
        send_message(chat_id, f"Question {i+1}/{len(CHECKLIST_ITEMS)}\n\n{CHECKLIST_ITEMS[i]}\n\nReponds par oui ou non")
    else:
        afficher_score(chat_id)

def afficher_score(chat_id):
    session = sessions[chat_id]
    reponses = session["reponses"]
    oui = sum(1 for r in reponses if r == "oui")
    total = len(reponses)
    pct = round(oui / total * 100)
    session["score"] = pct
    session["etape"] = "trade_pris"

    details = ""
    for i, item in enumerate(CHECKLIST_ITEMS):
        emoji = "OK" if reponses[i] == "oui" else "X"
        details += f"{emoji} {item}\n"

    msg = f"RESULTAT CHECKLIST\n\n{details}\nScore : {oui}/{total} ({pct}%)\n"
    if pct == 100:
        msg += "Tous les criteres valides"
    elif pct >= 75:
        msg += "Majoritairement valide"
    else:
        msg += "Trop de criteres manquants"

    msg += "\n\nAs-tu pris le trade ? (oui/non)"
    send_message(chat_id, msg)

def demander_donnees_trade(chat_id):
    sessions[chat_id]["etape"] = "actif"
    sessions[chat_id]["trade"] = {}
    send_message(chat_id, "Quel actif ? (ex: BTCUSDT, EURUSD, AAPL)")

def enregistrer_session(chat_id, trade_pris):
    session = sessions[chat_id]
    t = time.localtime()
    date = time.strftime("%d/%m/%Y", t)
    heure = time.strftime("%H:%M", t)
    jour = JOURS[t.tm_wday]

    trade = session.get("trade", {})
    capital = float(trade.get("capital", 0))
    pct_risque = float(trade.get("pct_risque", 0))
    montant_risque = round(capital * pct_risque / 100, 2)
    entree = float(trade.get("entree", 0))
    sl = float(trade.get("sl", 0))
    tp = float(trade.get("tp", 0))

    rr = "N/A"
    if entree and sl and tp:
        diff_entree_sl = abs(entree - sl)
        diff_entree_tp = abs(tp - entree)
        if diff_entree_sl > 0:
            rr = round(diff_entree_tp / diff_entree_sl, 2)

    reponses = session["reponses"]
    details_checklist = {}
    for i, item in enumerate(CHECKLIST_ITEMS):
        details_checklist[item] = reponses[i] if i < len(reponses) else "non"

    payload = {
        "date": date,
        "heure": heure,
        "jour": jour,
        "actif": trade.get("actif", "N/A"),
        "marche": trade.get("marche", "N/A"),
        "direction": trade.get("direction", "N/A"),
        "capital": capital,
        "pctRisque": pct_risque,
        "montantRisque": montant_risque,
        "entree": entree,
        "sl": sl,
        "tp": tp,
        "rr": rr,
        "score": session["score"],
        "tradePris": "Oui" if trade_pris else "Non",
        "checklist": details_checklist
    }

    envoyer_vers_sheets(payload)

    historique.append({
        "date": date,
        "heure": heure,
        "jour": jour,
        "score": session["score"],
        "trade_pris": trade_pris,
        "actif": trade.get("actif", "N/A")
    })

    msg = f"Session enregistree dans ton journal\n\nDate : {date} {heure} ({jour})\nScore checklist : {session['score']}%\nTrade pris : {'Oui' if trade_pris else 'Non'}"
    if trade_pris:
        msg += f"\nActif : {trade.get('actif', 'N/A')}\nDirection : {trade.get('direction', 'N/A')}\nR/R : {rr}"
    send_message(chat_id, msg)
    del sessions[chat_id]

def envoyer_historique(chat_id):
    if not historique:
        send_message(chat_id, "Pas encore d'historique. Lance une checklist avec 'checklist'")
        return

    msg = "HISTORIQUE DES SESSIONS\n\n"
    for h in historique[-10:]:
        trade_info = f" - {h['actif']}" if h['trade_pris'] else ""
        msg += f"{h['date']} {h['heure']} ({h['jour']}){trade_info} - Score: {h['score']}% - Trade: {'Oui' if h['trade_pris'] else 'Non'}\n"

    total = len(historique)
    moyenne = round(sum(h['score'] for h in historique) / total)
    trades_pris = sum(1 for h in historique if h['trade_pris'])
    msg += f"\nTotal sessions : {total}"
    msg += f"\nTrades pris : {trades_pris}"
    msg += f"\nScore moyen checklist : {moyenne}%"
    send_message(chat_id, msg)

def handle_message(chat_id, text):
    text = text.lower().strip()
    session = sessions.get(chat_id)

    if text in ["checklist", "/checklist", "/start", "start"]:
        envoyer_checklist(chat_id)
        return

    if text in ["historique", "/historique"]:
        envoyer_historique(chat_id)
        return

    if not session:
        send_message(chat_id, "Tape 'checklist' pour lancer la checklist\nTape 'historique' pour voir tes sessions")
        return

    etape = session["etape"]

    if etape == "checklist":
        if text in ["oui", "non"]:
            question_suivante(chat_id, text)
        else:
            send_message(chat_id, "Reponds uniquement par oui ou non")

    elif etape == "trade_pris":
        if text == "oui":
            demander_donnees_trade(chat_id)
        elif text == "non":
            enregistrer_session(chat_id, False)
        else:
            send_message(chat_id, "Reponds par oui ou non")

    elif etape == "actif":
        session["trade"]["actif"] = text.upper()
        session["etape"] = "marche"
        send_message(chat_id, "Quel marche ?\n1 - Crypto\n2 - Forex\n3 - Actions\n\nReponds par 1, 2 ou 3")

    elif etape == "marche":
        marches = {"1": "Crypto", "2": "Forex", "3": "Actions"}
        if text in marches:
            session["trade"]["marche"] = marches[text]
            session["etape"] = "direction"
            send_message(chat_id, "Direction du trade ?\n1 - Long\n2 - Short\n\nReponds par 1 ou 2")
        else:
            send_message(chat_id, "Reponds par 1, 2 ou 3")

    elif etape == "direction":
        if text == "1":
            session["trade"]["direction"] = "Long"
            session["etape"] = "capital"
            send_message(chat_id, "Quel est ton capital actuel ? (ex: 10000)")
        elif text == "2":
            session["trade"]["direction"] = "Short"
            session["etape"] = "capital"
            send_message(chat_id, "Quel est ton capital actuel ? (ex: 10000)")
        else:
            send_message(chat_id, "Reponds par 1 ou 2")

    elif etape == "capital":
        try:
            session["trade"]["capital"] = float(text.replace(",", "."))
            session["etape"] = "pct_risque"
            send_message(chat_id, "Quel pourcentage de ton capital tu risques sur ce trade ? (ex: 1.5)")
        except:
            send_message(chat_id, "Entre un nombre valide (ex: 10000)")

    elif etape == "pct_risque":
        try:
            pct = float(text.replace(",", ".").replace("%", ""))
            session["trade"]["pct_risque"] = pct
            session["etape"] = "entree"
            send_message(chat_id, "Prix d'entree ? (ex: 42500)")
        except:
            send_message(chat_id, "Entre un nombre valide (ex: 1.5)")

    elif etape == "entree":
        try:
            session["trade"]["entree"] = float(text.replace(",", "."))
            session["etape"] = "sl"
            send_message(chat_id, "Prix du Stop-Loss ? (ex: 41000)")
        except:
            send_message(chat_id, "Entre un nombre valide")

    elif etape == "sl":
        try:
            session["trade"]["sl"] = float(text.replace(",", "."))
            session["etape"] = "tp"
            send_message(chat_id, "Prix du Take Profit ? (ex: 45000)")
        except:
            send_message(chat_id, "Entre un nombre valide")

    elif etape == "tp":
        try:
            session["trade"]["tp"] = float(text.replace(",", "."))
            enregistrer_session(chat_id, True)
        except:
            send_message(chat_id, "Entre un nombre valide")

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
                text = message.get("text", "")
                if chat_id and text:
                    handle_message(chat_id, text)
        except Exception as e:
            print(f"Erreur: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
