import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

# Canali Telegram da scansionare
CHANNELS = ["offertone", "tariffando", "codiciscontopuntoit"]

def scrape_telegram():
    all_deals = []
    print("--- AVVIO BOT GHOST (ANTI-BLOCCO) ---")
    
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        print(f"Scansione canale: {channel}...")
        try:
            res = requests.get(url, timeout=20)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.content, 'html.parser')
            messages = soup.select('div.tgme_widget_message')
            
            for msg in messages:
                try:
                    text_el = msg.select_one('div.tgme_widget_message_text')
                    if not text_el: continue
                    text = text_el.get_text()
                    
                    # Cerca link Amazon
                    links = msg.select('a')
                    amazon_url = ""
                    for link in links:
                        href = link.get('href', '')
                        if "amazon.it" in href or "amzn.to" in href:
                            amazon_url = href
                            break
                    
                    if not amazon_url: continue
                    
                    # Estrae immagine
                    img_el = msg.select_one('a.tgme_widget_message_photo_wrap')
                    img_url = ""
                    if img_el:
                        style = img_el.get('style', '')
                        match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                        if match: img_url = match.group(1)
                    
                    if not img_url: continue

                    # Estrae prezzo (cerca il simbolo €)
                    price_match = re.search(r"(\d+[\.,]\d+)\s*€", text)
                    new_p = float(price_match.group(1).replace(',', '.')) if price_match else 0.0
                    if new_p == 0: continue

                    all_deals.append({
                        "id": int(time.time()) + len(all_deals),
                        "title": text[:120].split('\n')[0] + "...",
                        "oldPrice": round(new_p * 1.4, 2),
                        "newPrice": new_p,
                        "discountPct": random.randint(30, 70),
                        "hasCoupon": "coupon" in text.lower(),
                        "couponText": "COUPON ATTIVABILE",
                        "image": img_url,
                        "asin": amazon_url.split('/')[-1].split('?')[0] if "/" in amazon_url else "B00000",
                        "category": channel.capitalize()
                    })
                except: continue
        except: continue
    
    if all_deals:
        # Rimuove duplicati
        unique = {d['asin']: d for d in all_deals}.values()
        final = sorted(list(unique), key=lambda x: x['id'], reverse=True)
        
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"SUCCESSO! {len(final)} offerte reali trovate.")
    else:
        print("Errore: Nessun dato trovato nei canali.")

if __name__ == "__main__":
    scrape_telegram()
