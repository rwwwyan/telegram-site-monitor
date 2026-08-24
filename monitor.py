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


def telegram_request(method, **kwargs):
    response = requests.post(
        f"{TELEGRAM_API}/{method}",
        **kwargs
    )
    response.raise_for_status()
    return response.json()


def send_telegram(message):
    telegram_request(
        "sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )


def remove_webhook():
    try:
        result = requests.get(
            f"{TELEGRAM_API}/deleteWebhook",
            params={"drop_pending_updates": False},
            timeout=10
        )

        print("Telegram webhook:", result.text)

    except Exception as error:
        print("Erro ao remover webhook:", error)


def check_telegram():
    global last_update_id

    try:
        response = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={
                "offset": last_update_id + 1,
                "timeout": 2
            },
            timeout=10
        )

        response.raise_for_status()

        updates = response.json().get("result", [])

        for update in updates:
            last_update_id = update["update_id"]

            message = update.get("message", {})
            text = message.get("text", "")
            chat_id = str(
                message.get("chat", {}).get("id", "")
            )

            print(
                f"Mensagem recebida: {text} "
                f"do chat {chat_id}"
            )

            if text == "/start" and chat_id == str(CHAT_ID):
                send_telegram(
                    "✅ BOT FUNCIONANDO!\n\n"
                    "Estou monitorando:\n"
                    f"{SITE_URL}\n\n"
                    "🔎 Verificação a cada 60 segundos."
                )

    except Exception as error:
        print("Erro Telegram:", error)


def get_site_hash():
    response = requests.get(
        SITE_URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    response.raise_for_status()

    return hashlib.sha256(
        response.content
    ).hexdigest()


# Remove qualquer webhook antigo
remove_webhook()

# Teste automático do Telegram
try:
    send_telegram(
        "🟢 MONITOR ONLINE!\n\n"
        f"Site monitorado:\n{SITE_URL}"
    )
    print("Mensagem de teste enviada para o Telegram.")

except Exception as error:
    print("ERRO AO ENVIAR TESTE PARA TELEGRAM:", error)


print(f"Monitorando: {SITE_URL}")


try:
    previous_hash = get_site_hash()
    print("Estado inicial salvo.")

except Exception as error:
    print("Erro ao acessar o site:", error)


while True:

    check_telegram()

    try:
        current_hash = get_site_hash()

        if current_hash != previous_hash:

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
