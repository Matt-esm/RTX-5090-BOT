from flask import Flask, render_template_string, redirect, url_for
import threading
import requests
from bs4 import BeautifulSoup
import time

app = Flask(__name__)

BOT_TOKEN = "8094482734:AAHMPOdXAJSIACxs14S9urJCtNB-MXZf5lg"
CHAT_ID = "5221347852"
CHECK_INTERVAL = 60  # secondes
NVIDIA_URL = "https://marketplace.nvidia.com/fr-fr/consumer/graphics-cards/?locale=fr-fr&gpu=RTX%205090"

# Historique des statuts (jusqu'à 10 entrées)
history = []


def check_stock_loop():
    while True:
        perform_check(automated=True)
        time.sleep(CHECK_INTERVAL)


def perform_check(automated=False):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(NVIDIA_URL, headers=headers, timeout=5)
        soup = BeautifulSoup(response.text, "html.parser")

        now = time.strftime("%d/%m/%Y à %H:%M:%S")
        status = {
            "time": now,
            "available": False,
            "text":
            "🔴 Rupture automatique" if automated else "🔴 Rupture (manuel)"
        }

        if "Rupture De Stock" not in soup.text:
            status["available"] = True
            status["text"] = "🟢 DISPONIBLE !"
            send_telegram("🚨 RTX 5090 FE DISPONIBLE !!!\n" + NVIDIA_URL)

        history.insert(0, status)
        if len(history) > 10:
            history.pop()
    except Exception as e:
        history.insert(
            0, {
                "time": time.strftime("%d/%m/%Y à %H:%M:%S"),
                "available": False,
                "text": f"❌ Erreur : {e}"
            })


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.get(url, params={"chat_id": CHAT_ID, "text": message}, timeout=5)


@app.route("/")
def home():
    html = """
    <html>
    <head>
        <title>RTX 5090 FE - Suivi</title>
        <style>
            body { font-family: Arial, sans-serif; background: #121212; color: white; padding: 20px; }
            h1 { color: #00ff99; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 10px; border: 1px solid #444; text-align: left; }
            .green { color: #00ff99; font-weight: bold; }
            .red { color: #ff5555; font-weight: bold; }
            .error { color: #ffcc00; }
            .footer { margin-top: 30px; font-size: 12px; color: #aaa; }
            .btn { padding:10px 20px; margin-bottom: 10px; border:none; font-weight:bold; cursor:pointer; }
            .test { background:#00ff99; color:#000; }
            .check { background:#ffaa00; color:#000; }
        </style>
        <meta http-equiv="refresh" content="5">
    </head>
    <body>
        <h1>Suivi de stock : NVIDIA RTX 5090 FE</h1>

        <form action="/test" method="get">
            <button type="submit" class="btn test">📩 Envoyer un message test Telegram</button>
        </form>

        <form action="/check" method="get">
            <button type="submit" class="btn check">🔍 Forcer une vérification maintenant</button>
        </form>

        <table>
            <tr><th>Heure</th><th>Statut</th></tr>
            {% for s in history %}
                <tr>
                    <td>{{ s.time }}</td>
                    <td>
                        {% if 'Erreur' in s.text %}
                            <span class="error">❌ {{ s.text }}</span>
                        {% elif s.available %}
                            <span class="green">{{ s.text }}</span>
                        {% else %}
                            <span class="red">{{ s.text }}</span>
                        {% endif %}
                    </td>
                </tr>
            {% endfor %}
        </table>

        <div class="footer">Dernière mise à jour : {{ history[0].time if history else "..." }}</div>
    </body>
    </html>
    """
    return render_template_string(html, history=history)


@app.route("/test")
def send_test_message():
    send_telegram("✅ Ceci est un message test depuis le bot RTX 5090 FE.")
    return redirect(url_for("home"))


@app.route("/check")
def manual_check():

    def run_manual_check():
        try:
            perform_check(automated=False)
        except Exception as e:
            print("Erreur thread /check :", e)

    threading.Thread(target=run_manual_check, daemon=True).start()
    return redirect(url_for("home"))


# Lancer la vérification auto
threading.Thread(target=check_stock_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
