import requests
from bs4 import BeautifulSoup
import json
import time
import random
import sys
import re

# --- CONFIGURAZIONE ---
TARGET_URLS = [
    "https://www.amazon.it/s?k=offerte+lampo&i=specialty-aps&srs=11400615031&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=elettronica&i=electronics&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=informatica&i=computers&rh=p_8%3A20-95"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9",
    "Referer": "https://www.google.it/"
}

def clean_price_string(price_str):
    """Trasforma '1.299,00 €' in 1299.00"""
    if not price_str: return 0.0
    # Rimuove tutto tranne numeri, virgola e punto
    price_str = "".join(c for c in price_str if c.isdigit() or c in ",.")
    
    # Se c'è sia punto che virgola (es. 1.299,00)
    if "." in price_str and "," in price_str:
        price_str = price_str.replace(".", "").replace(",", ".")
    # Se c'è solo la virgola (es. 12,99)
    elif "," in price_str:
        price_str = price_str.replace(",", ".")
        
    try:
        return float(price_str)
    except:
        return 0.0

def scrape_page(url):
    print(f"Scansione: {url[:60]}...")
    results = []
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200: return []
        
        soup = BeautifulSoup(res.content, 'html.parser')
        items = soup.select('div[data-component-type="s-search-result"]')

        for item in items:
            try:
                asin = item.get('data-asin')
                if not asin: continue

                title_el = item.select_one('h2 span')
                title = title_el.text.strip() if title_el else "Prodotto Amazon"

                img_el = item.select_one('img.s-image')
                image = img_el.get('src') if img_el else ""

                # Prezzo attuale (Scontato)
                # Amazon usa classi diverse. Cerchiamo la più comune.
                price_new_container = item.select_one('span.a-price span.a-offscreen')
                new_p = clean_price_string(price_new_container.text) if price_new_container else 0.0

                # Prezzo originale (Barrato)
                price_old_container = item.select_one('span.a-price.a-text-price span.a-offscreen')
                old_p = clean_price_string(price_old_container.text) if price_old_container else 0.0

                # Se non troviamo il prezzo barrato, a volte è in un'altra classe
                if old_p == 0:
                    alt_old = item.select_one('span.a-text-strike')
                    old_p = clean_price_string(alt_old.text) if alt_old else 0.0

                # Calcolo sconto reale
                discount = 0
                if old_p > new_p and old_p > 0:
                    discount = int(((old_p - new_p) / old_p) * 100)
                
                # Sanity check: se lo sconto è assurdo (>98%) o negativo, è un errore di lettura
                if discount > 98 or discount < 0:
                    discount = 0
                    old_p = new_p

                has_coupon = "coupon" in item.text.lower() or "risparmia" in item.text.lower()

                # Filtro richiesto: 20-95% o Coupon
                if (discount >= 20 and discount <= 97) or has_coupon:
                    results.append({
                        "id": int(time.time()) + random.randint(0, 1000),
                        "title": title,
                        "oldPrice": round(old_p, 2),
                        "newPrice": round(new_p, 2),
                        "discountPct": discount,
                        "hasCoupon": has_coupon,
                        "couponText": "COUPON DISPONIBILE" if has_coupon else "",
                        "image": image,
                        "asin": asin,
                        "category": "Amazon",
                        "description": f"Sconto reale del {discount}%"
                    })
                    print(f"OK: {asin} - {new_p}€ (Sconto {discount}%)")
            except:
                continue
        return results
    except Exception as e:
        print(f"Errore: {e}")
        return []

if __name__ == "__main__":
    all_deals = []
    for url in TARGET_URLS:
        found = scrape_page(url)
        all_deals.extend(found)
        time.sleep(random.uniform(4, 8))

    if all_deals:
        unique = {d['asin']: d for d in all_deals}.values()
        final = sorted(list(unique), key=lambda x: x['id'], reverse=True)

        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"COMPLETATO: {len(final)} offerte reali salvate!")
    else:
        print("ERRORE: Nessuna offerta trovata. Verifica i selettori o blocchi Amazon.")
        sys.exit(1)

