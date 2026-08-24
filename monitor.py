import hashlib
import os
import time

import requests

SITE_URL = "https://cyberleek.perma.online/"
CHECK_INTERVAL = 60

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

previous_hash = None
last_update_id = 0


def get_site_hash():
    response = requests.get(
        SITE_URL,
        timeout=30,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    response.raise_for_status()

    return hashlib.sha256(response.content).hexdigest()


def send_telegram(message):
    response = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


def check_telegram():
    global last_update_id

    try:
        response = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={
                "offset": last_update_id + 1,
                "timeout": 1
            },
            timeout=5
        )

        response.raise_for_status()

        updates = response.json().get("result", [])

        for update in updates:
            last_update_id = update["update_id"]

            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = str(message.get("chat", {}).get("id", ""))

            if text == "/start" and chat_id == str(CHAT_ID):
                send_telegram(
                    "✅ Bot funcionando!\n\n"
                    "Estou monitorando o site:\n"
                    f"{SITE_URL}\n\n"
                    "🔎 Verificação: a cada 60 segundos."
                )

    except Exception as error:
        print("Erro Telegram:", error)


print(f"Monitorando: {SITE_URL}")

try:
    previous_hash = get_site_hash()
    print("Estado inicial salvo.")

except Exception as error:
    print("Erro ao acessar o site:", error)


while True:

    # Verifica comandos do Telegram
    check_telegram()

    # Verifica o site
    try:
        current_hash = get_site_hash()

        if previous_hash is None:
            previous_hash = current_hash

        elif current_hash != previous_hash:
            print("ALTERAÇÃO DETECTADA!")

            send_telegram(
                "🚨 ATUALIZAÇÃO DETECTADA!\n\n"
                f"O site foi alterado:\n{SITE_URL}"
            )

            previous_hash = current_hash

        else:
            print("Nenhuma alteração.")

    except Exception as error:
        print("Erro ao verificar o site:", error)

    time.sleep(CHECK_INTERVAL)
