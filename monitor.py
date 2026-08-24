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
                    "Estou monitorando somente a aba LEEKS:\n"
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

        # Espera o JavaScript carregar os dados
        time.sleep(8)

        # Procura o título LEEKS
        leeks = page.get_by_text(
            "LEEKS",
            exact=True
        ).first

        if leeks.count() == 0:
            print("ERRO: seção LEEKS não encontrada.")
            return ""

        # Pega o elemento pai da seção LEEKS
        parent = leeks.locator("..")

        # Dá tempo para o conteúdo dinâmico carregar
        time.sleep(2)

        content = parent.inner_text()

        # Normaliza o conteúdo
        lines = []

        for line in content.splitlines():

            line = " ".join(line.split())

            if line:
                lines.append(line)

        content = "\n".join(lines)

        print(
            f"LEEKS capturado: "
            f"{len(content)} caracteres"
        )

        return content

    except Exception as error:

        print(
            "Erro ao capturar LEEKS:",
            error
        )

        return ""

    finally:

        page.close()


def get_content_hash(content):

    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()


print("===================================")
print(" CYBERLEEK LEEKS MONITOR")
print("===================================")
print(f"Site: {SITE_URL}")
print(f"Intervalo: {CHECK_INTERVAL} segundos")
print("Monitorando SOMENTE: LEEKS")
print("")


remove_webhook()


with sync_playwright() as playwright:

    browser = playwright.chromium.launch(
        headless=True
    )

    print("Navegador iniciado.")

    # Teste automático do Telegram
    send_telegram(
        "🟢 MONITOR ONLINE!\n\n"
        f"Site monitorado:\n{SITE_URL}\n\n"
        "📌 Área monitorada: LEEKS\n"
        "🌐 Navegador automático ativado.\n"
        "🔎 Verificação a cada 60 segundos."
    )

    try:

        initial_content = get_rendered_page(
            browser
        )

        if initial_content:

            previous_hash = get_content_hash(
                initial_content
            )

            print("Estado inicial de LEEKS salvo.")

        else:

            print(
                "Não foi possível obter "
                "o conteúdo de LEEKS."
            )

    except Exception as error:

        print(
            "ERRO AO INICIAR MONITOR:",
            error
        )

    while True:

        # Verifica comandos do Telegram
        check_telegram()

        try:

            print("")
            print("Verificando LEEKS...")

            current_content = get_rendered_page(
                browser
            )

            if not current_content:

                print(
                    "LEEKS vazio ou não encontrado."
                )

            else:

                current_hash = get_content_hash(
                    current_content
                )

                if previous_hash is None:

                    previous_hash = current_hash

                    print(
                        "Estado inicial salvo."
                    )

                elif current_hash != previous_hash:

                    print(
                        "🚨 ALTERAÇÃO EM LEEKS DETECTADA!"
                    )

                    send_telegram(
                        "🚨 ATUALIZAÇÃO EM LEEKS!\n\n"
                        f"Site:\n{SITE_URL}\n\n"
                        "📌 A seção LEEKS foi alterada."
                    )

                    previous_hash = current_hash

                else:

                    print(
                        "Nenhuma alteração em LEEKS."
                    )

        except Exception as error:

            print(
                "Erro ao verificar LEEKS:",
                error
            )

        time.sleep(CHECK_INTERVAL)
