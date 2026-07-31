import requests
from bs4 import BeautifulSoup
import json
import time
import random
import sys
import re

# CONFIGURAZIONE TARGET
TARGET_URLS = [
    "https://www.amazon.it/s?k=offerte+lampo&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=informatica&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=elettronica&rh=p_8%3A20-95"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}

def clean_price(p_str):
    if not p_str: return 0.0
    p_str = p_str.replace('.', '').replace(',', '.')
    try:
        res = re.findall(r"\d+\.\d+|\d+", p_str)
        return float(res[0]) if res else 0.0
    except:
        return 0.0

def scrape_page(url):
    print(f"Scansione in corso...")
    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code != 200: return []
        soup = BeautifulSoup(res.content, 'html.parser')
        items = soup.select('div[data-component-type="s-search-result"]')
        results = []
        for item in items:
            try:
                asin = item.get('data-asin')
                title = item.select_one('h2 span').text.strip()
                img = item.select_one('img.s-image').get('src')
                
                # Prezzo Nuovo
                p_new_el = item.select_one('span.a-price span.a-offscreen')
                p_new = clean_price(p_new_el.text) if p_new_el else 0.0
                
                # Prezzo Vecchio
                p_old_el = item.select_one('span.a-price.a-text-price span.a-offscreen')
                p_old = clean_price(p_old_el.text) if p_old_el else p_new
                
                # Sconto
                discount = int(((p_old - p_new) / p_old) * 100) if p_old > p_new else 0
                has_coupon = "coupon" in item.text.lower() or "risparmia" in item.text.lower()

                # Filtro richiesto: 20-97% o Coupon
                if (discount >= 20 and discount <= 97) or has_coupon:
                    results.append({
                        "id": int(time.time()) + random.randint(1, 1000),
                        "title": title,
                        "oldPrice": p_old,
                        "newPrice": p_new,
                        "discountPct": discount,
                        "hasCoupon": has_coupon,
                        "couponText": "COUPON DISPONIBILE" if has_coupon else "",
                        "image": img,
                        "asin": asin,
                        "category": "Amazon"
                    })
            except: continue
        return results
    except: return []

if __name__ == "__main__":
    all_deals = []
    for url in TARGET_URLS:
        all_deals.extend(scrape_page(url))
        time.sleep(random.uniform(5, 10))
    
    if all_deals:
        # Rimuove duplicati per ASIN
        unique = {d['asin']: d for d in all_deals}.values()
        final = sorted(list(unique), key=lambda x: x['discountPct'], reverse=True)
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"SUCCESSO: {len(final)} offerte reali salvate!")
    else:
        print("ERRORE: Nessun dato trovato.")
        sys.exit(1)
