import hashlib
import os
import time

import requests
from playwright.sync_api import sync_playwright


SITE_URL = "https://cyberleek.perma.online/"
CHECK_INTERVAL = 60

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

previous_hash = None
last_update_id = 0


def send_telegram(message):
    try:
        response = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            data={
                "chat_id": CHAT_ID,
                "text": message
            },
            timeout=30
        )

        response.raise_for_status()

        print("Telegram: mensagem enviada.")

    except Exception as error:
        print("Erro ao enviar Telegram:", error)


def remove_webhook():
    try:
        response = requests.get(
            f"{TELEGRAM_API}/deleteWebhook",
            params={
                "drop_pending_updates": False
            },
            timeout=10
        )

        print("Webhook:", response.text)

    except Exception as error:
        print("Erro webhook:", error)


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

            if text == "/start" and chat_id == str(CHAT_ID):

                send_telegram(
                    "✅ BOT FUNCIONANDO!\n\n"
                    "Estou monitorando o site:\n"
                    f"{SITE_URL}\n\n"
                    "🔎 Verificação: a cada 60 segundos."
                )

    except Exception as error:
        print("Erro Telegram:", error)


def get_rendered_page(browser):

    page = browser.new_page()

    try:

        print("Abrindo site...")

        page.goto(
            SITE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        # Dá tempo para o JavaScript carregar
        time.sleep(8)

        # Pega somente o texto visível da página
        text = page.locator("body").inner_text()

        # Normaliza espaços e linhas
        lines = []

        for line in text.splitlines():

            line = " ".join(line.split())

            if line:
                lines.append(line)

        content = "\n".join(lines)

        return content

    finally:
        page.close()


def get_content_hash(content):

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


print("===================================")
print(" CYBERLEEK SITE MONITOR")
print("===================================")
print(f"Site: {SITE_URL}")
print(f"Intervalo: {CHECK_INTERVAL} segundos")
print("")


remove_webhook()


with sync_playwright() as playwright:

    browser = playwright.chromium.launch(
        headless=True
    )

    print("Navegador iniciado.")

    # Teste do Telegram
    send_telegram(
        "🟢 MONITOR ONLINE!\n\n"
        f"Site monitorado:\n{SITE_URL}\n\n"
        "🌐 Navegador automático ativado.\n"
        "🔎 Verificação a cada 60 segundos."
    )

    try:

        initial_content = get_rendered_page(browser)

        previous_hash = get_content_hash(
            initial_content
        )

        print("Estado inicial salvo.")
        print(
            f"Tamanho do conteúdo: "
            f"{len(initial_content)} caracteres"
        )

    except Exception as error:

        print(
            "ERRO AO ABRIR SITE:",
            error
        )

    while True:

        # Verifica comandos do Telegram
        check_telegram()

        try:

            print("")
            print("Verificando site...")

            current_content = get_rendered_page(
                browser
            )

            current_hash = get_content_hash(
                current_content
            )

            if current_hash != previous_hash:

                print("🚨 ALTERAÇÃO DETECTADA!")

                send_telegram(
                    "🚨 ATUALIZAÇÃO DETECTADA!\n\n"
                    f"Site:\n{SITE_URL}\n\n"
                    "O conteúdo visível da página "
                    "foi alterado."
                )

                previous_hash = current_hash

            else:

                print("Nenhuma alteração.")

        except Exception as error:

            print(
                "Erro ao verificar site:",
                error
            )

        time.sleep(CHECK_INTERVAL)