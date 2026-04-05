import os
import json
import time
import urllib.request

TOKEN = os.environ.get("TOKEN")
API = f"https://api.telegram.org/bot{TOKEN}"
SHEETS_CHECKLIST = "https://script.google.com/macros/s/AKfycbxq3dgto7MHKgijoF1rQP35cbXE0EitKORqfzfMK04sBrurw9lSNOQvFpKuAwK8GDYl/exec"
SHEETS_LOG = "https://script.google.com/macros/s/AKfycby-virBrxLO66gNIP1c4sXcEO95aC1zSaUPnZ_oZGHf_r0nPR-2EIb9ok8NDb4TkMgc/exec"

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

STRATEGIES = ["Ichimoku", "SMA 20", "Support et resistance"]
EMOTIONS = ["Stress", "Excitation", "Calme", "Revenge trading", "Serein", "Agite", "Incertitude", "Logique", "Doute"]
JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

sessions = {}
historique = []
capital_actuel = {}

def send_message(chat_id, text):
    try:
        data = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(f"{API}/sendMessage", data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Erreur envoi message: {e}")

def get_updates(offset=None):
    url = f"{API}/getUpdates?timeout=30"
    if offset:
        url += f"&offset={offset}"
    with urllib.request.urlopen(url, timeout=35) as r:
        return json.loads(r.read()).get("result", [])

def envoyer_vers_sheets(url, payload):
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req)
        return json.loads(resp.read())
    except Exception as e:
        print(f"Erreur Sheets: {e}")
        return {}

def envoyer_checklist(chat_id):
    sessions[chat_id] = {
        "etape": "checklist",
        "reponses": [],
        "index": 0,
        "trade": {}
    }
    send_message(chat_id, f"CHECKLIST TRADING\nQuestion 1/{len(CHECKLIST_ITEMS)}\n\n{CHECKLIST_ITEMS[0]}\n\nReponds par oui ou non")

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
    sessions[chat_id]["trade"] = {}
    if chat_id in capital_actuel:
        sessions[chat_id]["trade"]["capital"] = capital_actuel[chat_id]
        sessions[chat_id]["etape"] = "symbol"
        send_message(chat_id, f"Capital actuel : {capital_actuel[chat_id]}$ (mis a jour automatiquement)\n\nQuel symbole ? (ex: GBPUSD, XAUUSD)")
    else:
        sessions[chat_id]["etape"] = "capital_init"
        send_message(chat_id, "Premier trade — quel est ton capital de depart ? (ex: 6000)")

def finaliser_entree(chat_id):
    session = sessions[chat_id]
    trade = session["trade"]
    t = time.localtime()
    date = time.strftime("%b %d, %Y", t)
    heure = time.strftime("%H:%M", t)
    jour = JOURS[t.tm_wday]

    payload_log = {
        "action": "entry",
        "symbol": trade.get("symbol"),
        "market": trade.get("market"),
        "direction": trade.get("direction"),
        "entryPrice": trade.get("entryPrice"),
        "capital": trade.get("capital"),
        "pctRisque": trade.get("pctRisque"),
        "openDate": date,
        "strategy": trade.get("strategy"),
        "target": trade.get("target"),
        "stopLoss": trade.get("stopLoss"),
        "emotions": trade.get("emotions"),
        "remarks": trade.get("remarks", "")
    }

    resp = envoyer_vers_sheets(SHEETS_LOG, payload_log)
    row_number = resp.get("row", "?")
    session["trade"]["row"] = row_number

    envoyer_vers_sheets(SHEETS_CHECKLIST, {
        "date": date, "heure": heure, "jour": jour,
        "actif": trade.get("symbol"),
        "marche": trade.get("market"),
        "direction": trade.get("direction"),
        "capital": trade.get("capital"),
        "pctRisque": trade.get("pctRisque"),
        "montantRisque": round(float(trade.get("capital", 0)) * float(trade.get("pctRisque", 0)) / 100, 2),
        "entree": trade.get("entryPrice"),
        "sl": trade.get("stopLoss"),
        "tp": trade.get("target"),
        "rr": "N/A",
        "score": session["score"],
        "tradePris": "Oui"
    })

    historique.append({
        "date": date, "heure": heure, "jour": jour,
        "score": session["score"], "trade_pris": True,
        "actif": trade.get("symbol"), "row": row_number
    })

    entree = float(trade.get("entryPrice", 0))
    sl = float(trade.get("stopLoss", 0))
    target = float(trade.get("target", 0))
    capital = float(trade.get("capital", 0))
    pct = float(trade.get("pctRisque", 0))
    diff_sl = abs(entree - sl)
    montant = round(capital * pct / 100, 2)
    quantity = round(montant / diff_sl, 2) if diff_sl > 0 else 0
    rr = round(abs(target - entree) / diff_sl, 1) if diff_sl > 0 else 0

    msg = f"Trade enregistre dans ton journal !\n\n"
    msg += f"Date : {date} {heure} ({jour})\n"
    msg += f"Symbole : {trade.get('symbol')}\n"
    msg += f"Direction : {trade.get('direction')}\n"
    msg += f"Entree : {entree}\n"
    msg += f"Stop-Loss : {sl}\n"
    msg += f"Target : {target}\n"
    msg += f"R/R : 1:{rr}\n"
    msg += f"Quantite : {quantity}\n"
    msg += f"Montant risque : {montant}$ ({pct}%)\n"
    msg += f"Score checklist : {session['score']}%\n\n"
    msg += f"Tape 'cloturer {row_number}' quand tu fermes ce trade"

    send_message(chat_id, msg)
    # Modification ici pour éviter le blocage
    session["etape"] = "en_attente_cloture"

def cloturer_trade(chat_id, row_number):
    sessions[chat_id] = {
        "etape": "exit_price",
        "row": row_number,
        "exit": {}
    }
    send_message(chat_id, f"Cloture du trade #{row_number}\n\nPrix de sortie ?")

def enregistrer_sortie(chat_id):
    session = sessions[chat_id]
    exit_data = session["exit"]
    t = time.localtime()
    exit_date = time.strftime("%b %d, %Y", t)

    payload = {
        "action": "exit",
        "row": session["row"],
        "exitPrice": exit_data.get("exitPrice"),
        "exitDate": exit_date,
        "fees": exit_data.get("fees", 0)
    }

    resp = envoyer_vers_sheets(SHEETS_LOG, payload)
    pnl = float(resp.get("pnl", 0))
    ancien_capital = capital_actuel.get(chat_id, 0)
    nouveau_capital = round(ancien_capital + pnl, 2)
    capital_actuel[chat_id] = nouveau_capital

    msg = f"Trade #{session['row']} cloture !\n\n"
    msg += f"P&L : {'+' if pnl >= 0 else ''}{pnl}$\n"
    msg += f"Ancien capital : {ancien_capital}$\n"
    msg += f"Nouveau capital : {nouveau_capital}$"

    send_message(chat_id, msg)
    if chat_id in sessions:
        del sessions[chat_id]

def envoyer_historique(chat_id):
    if not historique:
        send_message(chat_id, "Pas encore d'historique. Lance une checklist avec 'checklist'")
        return
    msg = "HISTORIQUE DES SESSIONS\n\n"
    for h in historique[-10:]:
        trade_info = f" - {h['actif']}" if h.get('trade_pris') else ""
        msg += f"{h['date']} ({h['jour']}){trade_info} - Score: {h['score']}% - Trade: {'Oui' if h['trade_pris'] else 'Non'}\n"
    total = len(historique)
    moyenne = round(sum(h['score'] for h in historique) / total) if total > 0 else 0
    trades_pris = sum(1 for h in historique if h['trade_pris'])
    msg += f"\nTotal sessions : {total}\nTrades pris : {trades_pris}\nScore moyen : {moyenne}%"
    send_message(chat_id, msg)

def handle_message(chat_id, text):
    text_lower = text.lower().strip()
    session = sessions.get(chat_id)

    # Commandes globales prioritaires
    if text_lower in ["checklist", "/checklist", "/start", "start"]:
        envoyer_checklist(chat_id)
        return

    if text_lower in ["historique", "/historique"]:
        envoyer_historique(chat_id)
        return

    if text_lower in ["reset_capital", "/reset_capital"]:
        if chat_id in capital_actuel:
            del capital_actuel[chat_id]
        send_message(chat_id, "Capital remis a zero. Le prochain trade te demandera ton nouveau capital de depart.")
        return

    if text_lower.startswith("cloturer "):
        parts = text_lower.split(" ")
        if len(parts) == 2 and parts[1].isdigit():
            cloturer_trade(chat_id, int(parts[1]))
            return

    if not session:
        send_message(chat_id, "Commandes disponibles :\n- checklist : lancer la checklist\n- historique : voir les sessions\n- cloturer [numero] : cloturer un trade\n- reset_capital : remettre le capital a zero")
        return

    etape = session.get("etape")

    if etape == "checklist":
        if text_lower in ["oui", "non"]:
            question_suivante(chat_id, text_lower)
        else:
            send_message(chat_id, "Reponds uniquement par oui ou non")

    elif etape == "trade_pris":
        if text_lower == "oui":
            demander_donnees_trade(chat_id)
        elif text_lower == "non":
            t = time.localtime()
            envoyer_vers_sheets(SHEETS_CHECKLIST, {
                "date": time.strftime("%d/%m/%Y", t),
                "heure": time.strftime("%H:%M", t),
                "jour": JOURS[t.tm_wday],
                "actif": "N/A", "marche": "N/A", "direction": "N/A",
                "capital": 0, "pctRisque": 0, "montantRisque": 0,
                "entree": 0, "sl": 0, "tp": 0, "rr": "N/A",
                "score": session["score"], "tradePris": "Non"
            })
            historique.append({
                "date": time.strftime("%d/%m/%Y", t),
                "heure": time.strftime("%H:%M", t),
                "jour": JOURS[t.tm_wday],
                "score": session["score"], "trade_pris": False, "actif": "N/A"
            })
            send_message(chat_id, f"Session enregistree. Score : {session['score']}%\nTrade non pris.")
            del sessions[chat_id]
        else:
            send_message(chat_id, "Reponds par oui ou non")

    elif etape == "capital_init":
        try:
            val = float(text.replace(",", "."))
            capital_actuel[chat_id] = val
            session["trade"]["capital"] = val
            session["etape"] = "symbol"
            send_message(chat_id, f"Capital enregistre : {val}$\n\nQuel symbole ? (ex: GBPUSD, XAUUSD)")
        except:
            send_message(chat_id, "Entre un nombre valide (ex: 6000)")

    elif etape == "symbol":
        session["trade"]["symbol"] = text.upper()
        session["etape"] = "market"
        send_message(chat_id, "Quel marche ?\n1 - Forex\n2 - Matiere premiere\n3 - Crypto\n4 - Actions")

    elif etape == "market":
        marches = {"1": "Forex", "2": "Matiere premiere", "3": "Crypto", "4": "Actions"}
        if text_lower in marches:
            session["trade"]["market"] = marches[text_lower]
            session["etape"] = "direction"
            send_message(chat_id, "Direction ?\n1 - Long\n2 - Short")
        else:
            send_message(chat_id, "Reponds par 1, 2, 3 ou 4")

    elif etape == "direction":
        if text_lower == "1":
            session["trade"]["direction"] = "Long"
        elif text_lower == "2":
            session["trade"]["direction"] = "Short"
        else:
            send_message(chat_id, "Reponds par 1 ou 2")
            return
        session["etape"] = "pct_risque"
        send_message(chat_id, "% du capital risque ? (ex: 1.5)")

    elif etape == "pct_risque":
        try:
            session["trade"]["pctRisque"] = float(text.replace(",", ".").replace("%", ""))
            session["etape"] = "entry_price"
            send_message(chat_id, "Prix d'entree ?")
        except:
            send_message(chat_id, "Entre un nombre valide (ex: 1.5)")

    elif etape == "entry_price":
        try:
            session["trade"]["entryPrice"] = float(text.replace(",", "."))
            session["etape"] = "stop_loss"
            send_message(chat_id, "Stop-Loss ?")
        except:
            send_message(chat_id, "Entre un nombre valide")

    elif etape == "stop_loss":
        try:
            session["trade"]["stopLoss"] = float(text.replace(",", "."))
            session["etape"] = "target"
            send_message(chat_id, "Target (Take Profit) ?")
        except:
            send_message(chat_id, "Entre un nombre valide")

    elif etape == "target":
        try:
            session["trade"]["target"] = float(text.replace(",", "."))
            session["etape"] = "strategy"
            strats = "\n".join([f"{i+1} - {s}" for i, s in enumerate(STRATEGIES)])
            send_message(chat_id, f"Strategie utilisee ?\n{strats}")
        except:
            send_message(chat_id, "Entre un nombre valide")

    elif etape == "strategy":
        try:
            idx = int(text_lower) - 1
            if 0 <= idx < len(STRATEGIES):
                session["trade"]["strategy"] = STRATEGIES[idx]
                session["etape"] = "emotions"
                emotions_list = "\n".join([f"{i+1} - {e}" for i, e in enumerate(EMOTIONS)])
                send_message(chat_id, f"Etat emotionnel ?\n{emotions_list}")
            else:
                send_message(chat_id, f"Choisis entre 1 et {len(STRATEGIES)}")
        except:
            send_message(chat_id, f"Choisis un numero entre 1 et {len(STRATEGIES)}")

    elif etape == "emotions":
        try:
            idx = int(text_lower) - 1
            if 0 <= idx < len(EMOTIONS):
                session["trade"]["emotions"] = EMOTIONS[idx]
                session["etape"] = "remarks"
                send_message(chat_id, "Remarques sur ce trade ? (ou tape 'non' pour passer)")
            else:
                send_message(chat_id, f"Choisis entre 1 et {len(EMOTIONS)}")
        except:
            send_message(chat_id, f"Choisis un numero entre 1 et {len(EMOTIONS)}")

    elif etape == "remarks":
        session["trade"]["remarks"] = "" if text_lower == "non" else text
        finaliser_entree(chat_id)

    elif etape == "exit_price":
        try:
            # Nettoyage pour accepter uniquement chiffres et points
            clean_val = "".join(c for c in text if c.isdigit() or c in ".,")
            session["exit"]["exitPrice"] = float(clean_val.replace(",", "."))
            session["etape"] = "fees"
            send_message(chat_id, "Frais (fees) ? (tape 0 si aucun)")
        except:
            send_message(chat_id, "Entre un prix de sortie valide (ex: 1.1234)")

    elif etape == "fees":
        try:
            # Nettoyage pour accepter uniquement chiffres et points
            clean_val = "".join(c for c in text if c.isdigit() or c in ".,")
            session["exit"]["fees"] = float(clean_val.replace(",", "."))
            enregistrer_sortie(chat_id)
        except:
            send_message(chat_id, "Entre un montant de frais valide (ex: 0 ou 1.5)")

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
            print(f"Erreur boucle principale: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
