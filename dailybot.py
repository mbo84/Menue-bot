def finde_menu_pdf():

    print("Suche aktuelles Menü-PDF über WordPress API...")

    api_url = "https://labocca.ch/wp-json/wp/v2/media"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    kandidaten = []

    try:
        for seite in range(1, 6):

            params = {
                "media_type": "application",
                "per_page": 100,
                "page": seite
            }

            response = requests.get(
                api_url,
                params=params,
                headers=headers,
                timeout=20
            )

            if response.status_code == 400:
                break

            response.raise_for_status()

            medien = response.json()

            if not medien:
                break

            for medium in medien:

                pdf_url = medium.get("source_url", "")

                if not pdf_url.lower().endswith(".pdf"):
                    continue

                dateiname = pdf_url.split("/")[-1].lower()

                score = 0

                # Aktuelle Kalenderwoche
                if re.search(
                    rf'(?<!\d)0?{KW_OHNE_NULL}(?!\d)',
                    dateiname
                ):
                    score += 10

                # Standort Grossacker
                if "grossacker" in dateiname:
                    score += 5

                # Menü-Bezeichnungen
                if any(wort in dateiname for wort in [
                    "menu",
                    "menue",
                    "tagesmenu",
                    "tagesmenue",
                    "menuplan",
                    "menueplan"
                ]):
                    score += 3

                # Aktueller Monat
                if f"/{JAHR}/{MONAT}/" in pdf_url:
                    score += 5

                # Nur aktuelle Kalenderwoche akzeptieren
                if score >= 10:
                    kandidaten.append((score, pdf_url))

        if not kandidaten:
            print("Kein passendes Menü-PDF gefunden.")
            return None

        kandidaten.sort(
            key=lambda x: x[0],
            reverse=True
        )

        print("\nGefundene PDFs:")

        for score, url in kandidaten:
            print(f"Score {score}: {url}")

        beste_url = kandidaten[0][1]

        print(f"\n✅ Gefunden: {beste_url}")

        return beste_url

    except Exception as e:

        print(f"Fehler bei WordPress API: {e}")

        return None
