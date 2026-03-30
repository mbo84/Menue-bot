import requests
import PyPDF2
import io
import datetime


# --- 1. AUTOMATISCHE DATUMSERKENNUNG ---
heute = datetime.date.today()
JAHR = heute.strftime("%Y")          
MONAT = heute.strftime("%m")         
KALENDERWOCHE = heute.strftime("%V") 

# --- 2. DEINE DATEN (HIER ANPASSEN) ---
# Ersetze dies durch die echte Webadresse deiner Kantine
BASIS_URL = "https://www.deine-kantine.ch/menues/" 
PDF_URL = f"{BASIS_URL}{JAHR}/{MONAT}/Tagesmenu_{KALENDERWOCHE}.pdf"

# Deine Lieblingsgerichte
SUCHBEGRIFFE = ["Bratwurst", "Schnitzel", "Pizza", "Cordon Bleu", "Cheeseburger"]

# Deine Telegram-Codes einfügen
TELEGRAM_BOT_TOKEN = "8619475311:AAFUlW3y1ZBF7naGJ_AzZdmkzq9of6GmDnQ"
TELEGRAM_CHAT_ID = "1019541586"
# ---------------------------------------

def sende_telegram_nachricht(text):
    """Schickt die Push-Nachricht auf dein Handy."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
        print("Nachricht erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden der Telegram-Nachricht: {e}")

def check_menu():
    """Lädt das PDF und sucht nach den Gerichten."""
    print(f"Prüfe aktuellen Menüplan unter: {PDF_URL}")
    try:
        # Gibt sich als normaler Browser aus, damit die Webseite den Download nicht blockiert
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(PDF_URL, headers=headers)
        response.raise_for_status() 
        
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        
        kompletter_text = ""
        for page in reader.pages:
            kompletter_text += page.extract_text()
            
        gefundene_menues = []
        for begriff in SUCHBEGRIFFE:
            if begriff.lower() in kompletter_text.lower():
                gefundene_menues.append(begriff)
                
        if gefundene_menues:
            nachricht = f"🚨 Treffer im Menüplan! Heute gibt es: {', '.join(gefundene_menues)}"
            sende_telegram_nachricht(nachricht)
            print("Treffer gefunden und Nachricht verschickt!")
        else:
            print("Heute leider keins deiner Lieblingsmenüs dabei.")
            
    except requests.exceptions.HTTPError:
        print("Fehler: Das PDF für diese Woche ist (noch) nicht online oder die URL ist falsch.")
    except Exception as e:
        print(f"Allgemeiner Fehler beim Überprüfen: {e}")

if __name__ == "__main__":
    check_menu()

