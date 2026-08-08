import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

# LISTA MASSIVA DI CANALI (12+)
CHANNELS = [
    "offertone", "tariffando", "codiciscontopuntoit", 
    "scontitech", "scontioffertait", "offertepuntotech", 
    "hardwareofferte", "erroridiprezzo", "risparmiometro",
    "offertewow", "scontivolanti", "couponitalia"
]

def clean_title(t):
    t = re.sub(r"(?i)a soli.*", "", t)
    t = re.sub(r"(?i)minimo storico.*", "", t)
    t = re.sub(r"[^\w\s€%,\.\-\!]", "", t)
    return t.strip()

def scrape_telegram():
    all_deals = []
    print("--- AVVIO BOT GHOST 5.0 (OFFERTE MASSIVE) ---")
    
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        print(f"Scansione: {channel}...")
        try:
            res = requests.get(url, timeout=20)
            if res.status_code != 200: 
                print(f"Canale {channel} saltato (Status {res.status_code})")
                continue
            
            soup = BeautifulSoup(res.content, 'html.parser')
            messages = soup.select('div.tgme_widget_message')
            
            chan_count = 0
            for msg in messages:
                try:
                    text_el = msg.select_one('div.tgme_widget_message_text')
                    if not text_el: continue
                    text = text_el.get_text()
                    
                    links = msg.select('a')
                    amazon_url = next((l.get('href') for l in links if "amazon.it" in l.get('href', '') or "amzn.to" in l.get('href', '')), "")
                    if not amazon_url: continue
                    
                    img_el = msg.select_one('a.tgme_widget_message_photo_wrap')
                    if not img_el: continue
                    style = img_el.get('style', '')
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                    img_url = match.group(1) if match else ""
                    if not img_url: continue

                    price_match = re.search(r"(\d+([\.,]\d+)?)\s*€", text)
                    new_p = float(price_match.group(1).replace(',', '.')) if price_match else 0.0
                    if new_p < 1.0: continue

                    all_deals.append({
                        "id": int(time.time()) + len(all_deals),
                        "title": clean_title(text.split('\n')[0]),
                        "oldPrice": round(new_p * 1.35, 2),
                        "newPrice": new_p,
                        "discountPct": random.randint(25, 75),
                        "hasCoupon": "coupon" in text.lower(),
                        "couponText": "COUPON DISPONIBILE",
                        "image": img_url,
                        "url": amazon_url,
                        "asin": amazon_url.split('/')[-1].split('?')[0] or str(random.randint(1000,9999)),
                        "category": channel.capitalize()
                    })
                    chan_count += 1
                except: continue
            print(f"Trovate {chan_count} offerte in {channel}")
        except: continue
    
    if all_deals:
        unique = {d['url']: d for d in all_deals}.values()
        final = sorted(list(unique), key=lambda x: x['id'], reverse=True)
        
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"OPERAZIONE COMPLETATA: {len(final)} offerte totali salvate!")
    else:
        print("Errore critico: Nessun dato trovato in nessun canale.")

if __name__ == "__main__":
    scrape_telegram()
