import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TOKEN")

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
☐ Mon stop-loss est à un niveau logique
☐ Je risque max 1-2% de mon capital sur ce trade
☐ Mon ratio risque/rendement est d'au moins 2:1
☐ La taille de position est calculée en fonction du stop
☐ Pas de trades corrélés ouverts qui amplifient le risque

*🧠 État psychologique*
☐ Je suis calme et concentré
☐ Je ne suis pas en mode revenge trading
☐ Je ne suis pas en surconfiance après une série de gains
☐ J'accepte d'avance la possibilité de perdre
☐ Je peux laisser tourner le trade sans surveiller en permanence

✅ *Tous les critères cochés ? Tu peux entrer.*
⚠️ *Un critère manquant ? Reconsidère le trade.*"""

async def send_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(CHECKLIST, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("checklist", send_checklist))
    app.add_handler(CommandHandler("start", send_checklist))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, send_checklist))
    print("Bot démarré...")
    app.run_polling()

if __name__ == "__main__":
    main()
