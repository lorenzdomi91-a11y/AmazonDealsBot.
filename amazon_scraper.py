import requests
from bs4 import BeautifulSoup
import json
import time
import random
import sys
import re

# CONFIGURAZIONE
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
]

TARGET_URLS = [
    "https://www.amazon.it/s?k=offerte+del+giorno&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=informatica&rh=p_8%3A20-95",
    "https://www.amazon.it/s?k=casa+e+cucina&rh=p_8%3A20-95"
]

def clean_p(s):
    if not s: return 0.0
    s = s.replace('.', '').replace(',', '.')
    try:
        n = re.findall(r"\d+\.\d+|\d+", s)
        return float(n[0]) if n else 0.0
    except: return 0.0

def run_scraper():
    all_deals = []
    print("Avvio Scansione Reale...")
    for url in TARGET_URLS:
        h = {"User-Agent": random.choice(USER_AGENTS), "Accept-Language": "it-IT,it;q=0.9"}
        try:
            time.sleep(random.uniform(5, 10))
            r = requests.get(url, headers=h, timeout=35)
            if r.status_code != 200: continue
            soup = BeautifulSoup(r.content, 'html.parser')
            items = soup.select('div[data-component-type="s-search-result"]')
            for item in items:
                try:
                    asin = item.get('data-asin')
                    if not asin: continue
                    title = item.select_one('h2 span').text.strip()
                    img = item.select_one('img.s-image').get('src')
                    p_new = clean_p(item.select_one('span.a-price span.a-offscreen').text)
                    p_old_el = item.select_one('span.a-price.a-text-price span.a-offscreen')
                    p_old = clean_p(p_old_el.text) if p_old_el else p_new
                    if p_new == 0: continue
                    discount = int(((p_old - p_new) / p_old) * 100) if p_old > p_new else 0
                    has_c = "coupon" in item.text.lower() or "risparmia" in item.text.lower()
                    if (discount >= 20 and discount <= 97) or has_c:
                        all_deals.append({
                            "id": int(time.time()) + random.randint(1, 1000),
                            "title": title, "oldPrice": round(p_old, 2), "newPrice": round(p_new, 2),
                            "discountPct": discount, "hasCoupon": has_c,
                            "couponText": "COUPON ATTIVABILE" if has_c else "",
                            "image": img, "asin": asin, "category": "Amazon Reale"
                        })
                except: continue
        except: continue

    if all_deals:
        unique = {d['asin']: d for d in all_deals}.values()
        final = sorted(list(unique), key=lambda x: x['discountPct'], reverse=True)
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"SUCCESSO: Salvate {len(final)} offerte REALI.")
    else:
        print("ERRORE: Amazon ha bloccato la scansione.")
        sys.exit(1)

if __name__ == "__main__":
    run_scraper()
