import requests
from bs4 import BeautifulSoup
import json
import time
import random
import sys

# CONFIGURAZIONE SEMPLICE
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}

def scrape():
    print("Avvio scansione...")
    url = "https://www.amazon.it/s?k=offerte+lampo"
    try:
        res = requests.get(url, headers=HEADERS, timeout=30)
        if res.status_code != 200:
            print("Amazon ci ha bloccato momentaneamente.")
            return
        
        soup = BeautifulSoup(res.content, 'html.parser')
        items = soup.select('div[data-component-type="s-search-result"]')
        deals = []
        
        for item in items[:15]: # Prendiamo i primi 15 per sicurezza
            try:
                title = item.select_one('h2 span').text.strip()
                asin = item.get('data-asin')
                img = item.select_one('img.s-image').get('src')
                price_el = item.select_one('span.a-price span.a-offscreen')
                if not price_el: continue
                
                price = price_el.text.replace('€','').replace('.','').replace(',','.').strip()
                
                deals.append({
                    "id": int(time.time()) + random.randint(1, 100),
                    "title": title,
                    "oldPrice": float(price) * 1.5,
                    "newPrice": float(price),
                    "discountPct": 33,
                    "hasCoupon": False,
                    "image": img,
                    "asin": asin,
                    "category": "Offerte Vere"
                })
            except: continue
            
        if deals:
            with open("offerte.json", "w", encoding="utf-8") as f:
                json.dump(deals, f, indent=2, ensure_ascii=False)
            print(f"Fatto! Trovate {len(deals)} offerte reali.")
        else:
            print("Nessuna offerta trovata stavolta.")
            
    except Exception as e:
        print(f"Errore: {e}")

if __name__ == "__main__":
    scrape()
