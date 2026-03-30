import requests
import PyPDF2
import io
import datetime

# --- 1. AUTOMATISCHE DATUMSERKENNUNG ---
heute = datetime.date.today()
JAHR = heute.strftime("%Y")          
MONAT = heute.strftime("%m")         
KALENDERWOCHE = heute.strftime("%V") 

# --- 2. HIER TRÄGST DU EINMALIG DIE FIXEN DATEN EIN ---
BASIS_URL = "https://www.deine-kantine.ch/menues/" 
PDF_URL = f"{BASIS_URL}{JAHR}/{MONAT}/Tagesmenu_{KALENDERWOCHE}.pdf"

print(f"Prüfe aktuellen Menüplan unter: {PDF_URL}")

# --- 3. DEINE NEUEN SUCHBEGRIFFE ---
SUCHBEGRIFFE = ["Bratwurst", "Cheeseburger"]

# --- 4. DEINE TELEGRAM DATEN ---
TELEGRAM_BOT_TOKEN = "DEIN_BOT_TOKEN_HIER_EINTRAGEN"
TELEGRAM_CHAT_ID = "DEINE_CHAT_ID_HIER_EINTRAGEN"
# -------------------------------------

def sende_telegram_nachricht(text):
    """Schickt die Push-Nachricht auf dein Handy."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, data=data)
        print("Nachricht erfolgreich gesendet!")
    except Exception as e:
        print(f"Fehler beim Senden: {e}")

def check_menu():
    """Lädt das PDF und sucht nach den Gerichten."""
    print("Lade Menüplan herunter...")
    try:
        response = requests.get(PDF_URL)
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
            # Die angepasste Benachrichtigung für dein Handy
            nachricht = f"🟢 Hopp San Galle! Menü-Alarm: Heute gibt es {', '.join(gefundene_menues)}!"
            sende_telegram_nachricht(nachricht)
        else:
            print("Heute leider weder Bratwurst noch Cheeseburger dabei.")
            
    except Exception as e:
        print(f"Fehler beim Überprüfen des Menüplans: {e}")

if __name__ == "__main__":
    check_menu()

