import requests
from bs4 import BeautifulSoup
import json
import time
import random
import sys
import re

# CONFIGURAZIONE AVANZATA
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
]

TARGET_URLS = [
    "https://www.amazon.it/s?k=offerte+del+giorno&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=informatica&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=casa+e+cucina&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=gaming&rh=p_8%3A20-95"
]

def clean_price(p_str):
    if not p_str: return 0.0
    # Gestione formato italiano: 1.299,00 -> 1299.00
    p_str = p_str.replace('.', '').replace(',', '.')
    try:
        nums = re.findall(r"\d+\.\d+|\d+", p_str)
        return float(nums[0]) if nums else 0.0
    except:
        return 0.0

def scrape_with_retries(url, max_retries=3):
    for i in range(max_retries):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "it-IT,it;q=0.9",
            "Referer": "https://www.google.it/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "DNT": "1"
        }
        try:
            print(f"Scansione: {url[:50]}... (Tentativo {i+1})")
            time.sleep(random.uniform(5, 12))
            response = requests.get(url, headers=headers, timeout=40)
            
            if response.status_code == 200 and "captcha" not in response.text.lower():
                return response.content
            print(f"Bloccato o errore {response.status_code}. Riprovo...")
        except Exception as e:
            print(f"Errore connessione: {e}")
    return None

def scrape_amazon():
    all_deals = []
    print("--- AVVIO SCRAPER OTTIMIZZATO 2026 ---")
    
    for url in TARGET_URLS:
        content = scrape_with_retries(url)
        if not content: continue

        soup = BeautifulSoup(content, 'html.parser')
        items = soup.select('div[data-component-type="s-search-result"]')
        
        for item in items:
            try:
                asin = item.get('data-asin')
                if not asin: continue
                
                title_el = item.select_one('h2 span')
                title = title_el.text.strip() if title_el else ""
                if len(title) < 10: continue # Salta titoli incompleti
                
                img_el = item.select_one('img.s-image')
                image = img_el.get('src') if img_el else ""
                if not image.startswith("http"): continue
                
                # Prezzi
                p_new_el = item.select_one('span.a-price span.a-offscreen')
                new_p = clean_price(p_new_el.text) if p_new_el else 0.0
                
                p_old_el = item.select_one('span.a-price.a-text-price span.a-offscreen')
                old_p = clean_price(p_old_el.text) if p_old_el else new_p
                
                if new_p <= 0: continue
                
                # Sconto
                discount = 0
                if old_p > new_p:
                    discount = int(((old_p - new_p) / old_p) * 100)
                
                has_coupon = "coupon" in item.text.lower() or "risparmia" in item.text.lower()

                if (discount >= 20 and discount <= 97) or has_coupon:
                    all_deals.append({
                        "id": int(time.time()) + random.randint(1, 2000),
                        "title": title,
                        "oldPrice": round(old_p, 2),
                        "newPrice": round(new_p, 2),
                        "discountPct": discount,
                        "hasCoupon": has_coupon,
                        "couponText": "COUPON ATTIVABILE" if has_coupon else "",
                        "image": image,
                        "asin": asin,
                        "category": "Amazon Offerte"
                    })
            except: continue

    if all_deals:
        unique = {d['asin']: d for d in all_deals}.values()
        final = sorted(list(unique), key=lambda x: x['id'], reverse=True)
        
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"SUCCESSO: {len(final)} prodotti REALI salvati.")
    else:
        print("ERRORE: Amazon ha bloccato tutte le richieste.")
        sys.exit(1)

if __name__ == "__main__":
    scrape_amazon()
