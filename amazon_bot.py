import requests
from bs4 import BeautifulSoup

# 🔴 CAMBIA QUESTO LINK con il prodotto specifico che vuoi controllare!
URL = "https://www.amazon.it/dp/B0C1H12345"  # <-- Metti qui il link del prodotto

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

print("Controllo il prezzo del prodotto...")

pagina = requests.get(URL, headers=HEADERS)
soup = BeautifulSoup(pagina.content, 'html5lib')

# Cerca il prezzo intero (quello attuale)
prezzo_intero = soup.find('span', class_='a-price-whole')

# Cerca il prezzo barrato (lo sconto) - spesso si trova in un tag 'span' con classe 'a-text-strike'
prezzo_barrato = soup.find('span', class_='a-text-strike')

if prezzo_intero:
    prezzo = prezzo_intero.get_text(strip=True)
    print(f"💰 Prezzo attuale: € {prezzo}")

    if prezzo_barrato:
        vecchio_prezzo = prezzo_barrato.get_text(strip=True)
        print(f"⚠️  È in SCONTO! Prezzo originale: € {vecchio_prezzo}")
    else:
        print("❌ Nessuno sconto trovato per questo prodotto.")
else:
    print("❌ Impossibile leggere il prezzo. Amazon potrebbe avermi bloccato.")
