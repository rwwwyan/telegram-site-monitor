import hashlib
import json
import os
import time

import requests

SITE_URL = "https://cyberleek.perma.online/"
CHECK_INTERVAL = 60  # segundos

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

STATE_FILE = "site_state.json"


def get_site_hash():
    response = requests.get(
        SITE_URL,
        timeout=30,
        headers={
            "User-Agent": "Mozilla/5.0 (SiteMonitor/1.0)"
        }
    )
    response.raise_for_status()

    content = response.text.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message,
        },
        timeout=30
    )

    response.raise_for_status()


def load_previous_hash():
    if not os.path.exists(STATE_FILE):
        return None

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    return data.get("hash")


def save_hash(site_hash):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"hash": site_hash}, f)


def main():
    print(f"Monitorando: {SITE_URL}")

    previous_hash = load_previous_hash()

send_telegram(
    "✅ Bot conectado!\n\n"
    "O monitoramento do site foi iniciado."
)    
    while True:
        try:
            current_hash = get_site_hash()

            # Primeira execução: apenas salva o estado atual
            if previous_hash is None:
                save_hash(current_hash)
                previous_hash = current_hash
                print("Estado inicial salvo.")

            elif current_hash != previous_hash:
                print("ALTERAÇÃO DETECTADA!")

                send_telegram(
                    "🚨 ATUALIZAÇÃO DETECTADA!\n\n"
                    f"O site foi alterado:\n{SITE_URL}"
                )

                save_hash(current_hash)
                previous_hash = current_hash

            else:
                print("Nenhuma alteração.")

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
