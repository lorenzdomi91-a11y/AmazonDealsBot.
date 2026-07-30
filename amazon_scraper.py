
import requests
from bs4 import BeautifulSoup
import json
import time
import random

# --- CONFIGURAZIONE ---
# Il bot scansionerà le offerte reali filtrando per sconto 20-95%
TARGET_URLS = [
    "https://www.amazon.it/s?k=offerte+lampo&i=specialty-aps&srs=11400615031&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=elettronica&i=electronics&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=informatica&i=computers&rh=p_8%3A20-95"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9",
    "Referer": "https://www.google.it/"
}

def parse_price(p_str):
    if not p_str: return 0.0
    # Pulizia manuale senza libreria RE per massima compatibilità
    clean = "".join([c for d in p_str.split(",") for c in d if c.isdigit() or c == "."])
    try:
        return float(clean)
    except:
        return 0.0

def scrape_page(url):
    print(f"Scansione: {url[:50]}...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=20)
        if res.status_code != 200: return []
        
        soup = BeautifulSoup(res.content, 'html.parser')
        items = soup.select('div[data-component-type="s-search-result"]')
        results = []

        for item in items:
            try:
                title = item.select_one('h2 span').text.strip()
                asin = item.get('data-asin')
                image = item.select_one('img.s-image').get('src')

                p_new_el = item.select_one('span.a-price span.a-offscreen')
                p_old_el = item.select_one('span.a-price.a-text-price span.a-offscreen')
                
                new_p = parse_price(p_new_el.text) if p_new_el else 0.0
                old_p = parse_price(p_old_el.text) if p_old_el else new_p

                discount = 0
                if old_p > new_p and old_p > 0:
                    discount = int(((old_p - new_p) / old_p) * 100)

                # Controllo Coupon Avanzato
                item_text = item.text.lower()
                has_coupon = "coupon" in item_text or "risparmia" in item_text or "extra" in item_text
                coupon_text = "Vedi Coupon" if has_coupon else ""

                if (discount >= 20 and discount <= 97) or has_coupon:
                    results.append({
                        "id": int(time.time()) + random.randint(0, 1000),
                        "title": title,
                        "oldPrice": old_p,
                        "newPrice": new_p,
                        "discountPct": discount,
                        "hasCoupon": has_coupon,
                        "couponText": "Coupon disponibile" if has_coupon else "",
                        "image": image,
                        "asin": asin,
                        "category": "Amazon",
                        "description": "Offerta reale verificata."
                    })
            except:
                continue
        return results
    except:
        return []

if __name__ == "__main__":
    all_deals = []
    for url in TARGET_URLS:
        found = scrape_page(url)
        all_deals.extend(found)
        print(f"Trovate {len(found)} offerte in questa pagina.")
        time.sleep(random.uniform(3, 6))

    # Rimozione duplicati
    unique = {d['asin']: d for d in all_deals}.values()
    final = sorted(list(unique), key=lambda x: x['discountPct'], reverse=True)

    if len(final) > 0:
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"OPERAZIONE COMPLETATA: {len(final)} offerte reali caricate!")
    else:
        print("ERRORE: Amazon ha bloccato lo scraper. Riprova più tardi.")
