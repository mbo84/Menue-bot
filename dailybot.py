import requests
import PyPDF2
import io
import datetime
import re
import os
from urllib.parse import urljoin


# ==========================================================
# KONFIGURATION
# ==========================================================

heute = datetime.date.today()

JAHR = heute.strftime("%Y")
MONAT = heute.strftime("%m")
KALENDERWOCHE = heute.strftime("%V")
KW_OHNE_NULL = str(int(KALENDERWOCHE))

BASIS_URL = "https://labocca.ch/wp-content/uploads"

# Telegram-Daten aus GitHub Secrets / Environment
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


# ==========================================================
# WOCHENTAGE
# ==========================================================

WOCHENTAGE = [
    "Montag",
    "Dienstag",
    "Mittwoch",
    "Donnerstag",
    "Freitag",
    "Samstag",
    "Sonntag"
]


# ==========================================================
# PDF SUCHEN
# ==========================================================

def finde_menu_pdf():
    """
    Sucht automatisch nach dem aktuellen Menü-PDF.
    """

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    ordner_url = f"{BASIS_URL}/{JAHR}/{MONAT}/"

    print(f"Suche Menü-PDF in: {ordner_url}")

    try:
        response = requests.get(
            ordner_url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        html = response.text

        # Alle PDF-Links auf der Seite suchen
        pdf_links = re.findall(
            r'href=["\']([^"\']+\.pdf)["\']',
            html,
            re.IGNORECASE
        )

        kandidaten = []

        for link in pdf_links:

            pdf_url = urljoin(ordner_url, link)

            dateiname = pdf_url.split("/")[-1].lower()

            score = 0

            # Kalenderwoche
            if re.search(
                rf'(?<!\d)0?{re.escape(KW_OHNE_NULL)}(?!\d)',
                dateiname
            ):
                score += 10

            # Standort
            if "grossacker" in dateiname:
                score += 5

            # Typische Menü-Bezeichnungen
            if any(wort in dateiname for wort in [
                "menu",
                "menue",
                "tagesmenu",
                "tagesmenue",
                "menuplan",
                "menueplan"
            ]):
                score += 3

            if score > 0:
                kandidaten.append(
                    (score, pdf_url)
                )

        if not kandidaten:
            print("Keine passenden PDFs gefunden.")
            return None

        # Höchsten Score verwenden
        kandidaten.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print("\nGefundene Kandidaten:")

        for score, url in kandidaten:
            print(f"Score {score}: {url}")

        beste_url = kandidaten[0][1]

        print(f"\nVerwende: {beste_url}")

        return beste_url

    except Exception as e:

        print(
            f"Fehler beim Suchen des PDFs: {e}"
        )

        return None


# ==========================================================
# PDF HERUNTERLADEN UND TEXT EXTRAHIEREN
# ==========================================================

def lese_pdf(pdf_url):

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    print(f"Lade PDF: {pdf_url}")

    response = requests.get(
        pdf_url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    pdf_file = io.BytesIO(response.content)

    reader = PyPDF2.PdfReader(pdf_file)

    kompletter_text = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:
            kompletter_text += text + "\n"

    return kompletter_text


# ==========================================================
# HEUTIGES MENÜ EXTRAHIEREN
# ==========================================================

def finde_heutiges_menu(text):

    # 0 = Montag, 1 = Dienstag usw.
    index = heute.weekday()

    tag = WOCHENTAGE[index]

    print(f"Heutiger Tag: {tag}")

    # Am Wochenende normalerweise kein Menü
    if index >= 5:
        return None

    # Nächsten Wochentag bestimmen
    if index + 1 < len(WOCHENTAGE):
        naechster_tag = WOCHENTAGE[index + 1]
    else:
        naechster_tag = None

    # Zeilenumbrüche etwas normalisieren
    text = text.replace("\r", "\n")

    # Heutigen Tag suchen
    start_match = re.search(
        rf'\b{tag}\b',
        text,
        re.IGNORECASE
    )

    if not start_match:

        print(
            f"Konnte '{tag}' im PDF nicht finden."
        )

        return None

    start = start_match.end()

    # Bis zum nächsten Wochentag lesen
    if naechster_tag:

        ende_match = re.search(
            rf'\b{naechster_tag}\b',
            text[start:],
            re.IGNORECASE
        )

        if ende_match:

            ende = start + ende_match.start()

            menu = text[start:ende]

        else:

            menu = text[start:]

    else:

        menu = text[start:]

    # Aufräumen
    menu = menu.strip()

    # Mehrfache Leerzeilen reduzieren
    menu = re.sub(
        r'\n\s*\n+',
        '\n',
        menu
    )

    return menu


# ==========================================================
# TELEGRAM
# ==========================================================

def sende_telegram_nachricht(text):

    if not TELEGRAM_BOT_TOKEN:

        print("TELEGRAM_BOT_TOKEN fehlt!")
        return

    if not TELEGRAM_CHAT_ID:

        print("TELEGRAM_CHAT_ID fehlt!")
        return

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }

    try:

        response = requests.post(
            url,
            data=data,
            timeout=10
        )

        response.raise_for_status()

        print(
            "Telegram-Nachricht erfolgreich gesendet!"
        )

    except Exception as e:

        print(
            f"Fehler beim Senden: {e}"
        )


# ==========================================================
# HAUPTPROGRAMM
# ==========================================================

def check_menu():

    print("=" * 60)
    print("La Bocca Menü Bot")
    print("=" * 60)

    print(
        f"Datum: {heute.strftime('%d.%m.%Y')}"
    )

    print(
        f"Kalenderwoche: {KALENDERWOCHE}"
    )

    # ------------------------------------------------------
    # Wochenende?
    # ------------------------------------------------------

    if heute.weekday() >= 5:

        print(
            "Heute ist Wochenende. Kein Menüversand."
        )

        return

    # ------------------------------------------------------
    # PDF suchen
    # ------------------------------------------------------

    PDF_URL = finde_menu_pdf()

    if not PDF_URL:

        print(
            "Kein aktuelles Menü-PDF gefunden."
        )

        return

    # ------------------------------------------------------
    # PDF lesen
    # ------------------------------------------------------

    try:

        kompletter_text = lese_pdf(PDF_URL)

        print("\nPDF erfolgreich gelesen.")

    except Exception as e:

        print(
            f"Fehler beim Lesen des PDFs: {e}"
        )

        return

    # ------------------------------------------------------
    # heutiges Menü suchen
    # ------------------------------------------------------

    heutiges_menu = finde_heutiges_menu(
        kompletter_text
    )

    if not heutiges_menu:

        print(
            "Das heutige Menü konnte nicht gefunden werden."
        )

        return

    # ------------------------------------------------------
    # Telegram-Nachricht
    # ------------------------------------------------------

    tag = WOCHENTAGE[
        heute.weekday()
    ]

    nachricht = (
        f"🍽️ Mittagessen im La Bocca\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📅 {tag}, {heute.strftime('%d.%m.%Y')}\n\n"
        f"{heutiges_menu}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📄 Menüplan KW {KALENDERWOCHE}"
    )

    print("\nFolgende Nachricht wird gesendet:")
    print("-" * 60)
    print(nachricht)
    print("-" * 60)

    sende_telegram_nachricht(
        nachricht
    )


# ==========================================================
# START
# ==========================================================

if __name__ == "__main__":

    check_menu()
