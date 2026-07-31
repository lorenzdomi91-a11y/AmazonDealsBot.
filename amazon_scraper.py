import requests
from bs4 import BeautifulSoup
import json
import time
import random
import sys
import re

# CONFIGURAZIONE AVANZATA
# Cerchiamo di essere il più "umani" possibile
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]

TARGET_URLS = [
    "https://www.amazon.it/s?k=offerte+del+giorno&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=informatica&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=casa+e+cucina&rh=p_8%3A20-95"
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

def scrape_amazon():
    all_deals = []
    print("--- AVVIO SCRAPER PROFESSIONALE REALE ---")
    
    for url in TARGET_URLS:
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "it-IT,it;q=0.9",
            "Referer": "https://www.google.it/",
            "DNT": "1"
        }
        
        try:
            print(f"Navigazione su: {url[:60]}...")
            time.sleep(random.uniform(5, 12)) # Attesa lunga per simulare umano
            
            response = requests.get(url, headers=headers, timeout=35)
            
            if "api-services-support@amazon.com" in response.text or "captcha" in response.text.lower():
                print(f"ERRORE: Amazon ha rilevato il bot (CAPTCHA).")
                continue

            if response.status_code != 200:
                print(f"ERRORE: Status {response.status_code}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            items = soup.select('div[data-component-type="s-search-result"]')
            
            print(f"Trovati {len(items)} potenziali prodotti.")

            for item in items:
                try:
                    asin = item.get('data-asin')
                    if not asin: continue
                    
                    title_el = item.select_one('h2 span')
                    title = title_el.text.strip() if title_el else ""
                    
                    img_el = item.select_one('img.s-image')
                    image = img_el.get('src') if img_el else ""
                    
                    # Prezzi
                    p_new_el = item.select_one('span.a-price span.a-offscreen')
                    new_p = clean_price(p_new_el.text) if p_new_el else 0.0
                    
                    p_old_el = item.select_one('span.a-price.a-text-price span.a-offscreen')
                    old_p = clean_price(p_old_el.text) if p_old_el else new_p
                    
                    if new_p == 0: continue
                    
                    # Calcolo sconto reale
                    discount = 0
                    if old_p > new_p:
                        discount = int(((old_p - new_p) / old_p) * 100)
                    
                    # Rilevamento Coupon Reale
                    # Spesso Amazon mette un badge o un testo specifico
                    has_coupon = "coupon" in item.text.lower() or "risparmia" in item.text.lower()

                    # FILTRO RIGIDO: Solo sconti reali 20-95% o Coupon
                    if (discount >= 20 and discount <= 97) or has_coupon:
                        all_deals.append({
                            "id": int(time.time()) + random.randint(1, 1000),
                            "title": title,
                            "oldPrice": round(old_p, 2),
                            "newPrice": round(new_p, 2),
                            "discountPct": discount,
                            "hasCoupon": has_coupon,
                            "couponText": "COUPON ATTIVABILE" if has_coupon else "",
                            "image": image,
                            "asin": asin,
                            "category": "Amazon Reale"
                        })
                except:
                    continue
                    
        except Exception as e:
            print(f"Errore durante la scansione: {e}")

    # RIMOZIONE DUPLICATI E SALVATAGGIO
    if all_deals:
        unique = {d['asin']: d for d in all_deals}.values()
        # Ordina per sconto decrescente
        final = sorted(list(unique), key=lambda x: x['discountPct'], reverse=True)
        
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"SUCCESSO: Salvate {len(final)} offerte REALI.")
    else:
        print("ERRORE CRITICO: Nessun dato reale estratto. Amazon ha bloccato tutto.")
        sys.exit(1) # Forza fallimento su GitHub per avvisarci

if __name__ == "__main__":
