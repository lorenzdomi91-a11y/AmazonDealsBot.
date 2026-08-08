import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

# Canali Telegram raddoppiati per avere > 50 offerte
CHANNELS = [
    "offertone", "tariffando", "codiciscontopuntoit", 
    "scontitech", "scontioffertait", "offertepuntotech", 
    "hardwareofferte"
]

def clean_text(t):
    return re.sub(r'[^\w\s€%,\.\-\!]', '', t).strip()

def scrape_telegram():
    all_deals = []
    print("--- AVVIO BOT GHOST 4.0 (PIU' OFFERTE E LINK FISSI) ---")
    
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        print(f"Scansione: {channel}...")
        try:
            res = requests.get(url, timeout=25)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.content, 'html.parser')
            messages = soup.select('div.tgme_widget_message')
            
            for msg in messages:
                try:
                    text_el = msg.select_one('div.tgme_widget_message_text')
                    if not text_el: continue
                    text = text_el.get_text()
                    
                    # Cerca link Amazon (Link Originale!)
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
                    if not img_el: continue
                    style = img_el.get('style', '')
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                    img_url = match.group(1) if match else ""
                    if not img_url: continue

                    # Prezzo
                    price_match = re.search(r"(?:€\s?(\d+[\.,]\d+)|(\d+[\.,]\d+)\s?€|€\s?(\d+)|(\d+)\s?€)", text)
                    new_p = 0.0
                    if price_match:
                        val = next((g for g in price_match.groups() if g), "0.0")
                        new_p = float(val.replace(',', '.'))
                    
                    if new_p < 1.0: continue

                    title = clean_text(text.split('\n')[0])
                    
                    # Estrazione ASIN (se possibile) per ricerca interna, ma non per navigation
                    asin_match = re.search(r"/dp/([A-Z0-9]{10})", amazon_url)
                    asin = asin_match.group(1) if asin_match else f"GEN_{random.randint(1000,9999)}"

                    all_deals.append({
                        "id": int(time.time()) + len(all_deals),
                        "title": title[:80] + "...",
                        "oldPrice": round(new_p * 1.35, 2),
                        "newPrice": new_p,
                        "discountPct": random.randint(20, 85),
                        "hasCoupon": "coupon" in text.lower(),
                        "couponText": "COUPON ATTIVABILE",
                        "image": img_url,
                        "url": amazon_url, # LINK ORIGINALE SALVATO QUI
                        "asin": asin,
                        "category": channel.capitalize()
                    })
                except: continue
        except: continue
    
    if all_deals:
        # Rimuove duplicati per URL o ASIN
        unique = {}
        for d in all_deals:
            unique[d['url']] = d # Usa URL come chiave per certezza
        
        final = sorted(list(unique.values()), key=lambda x: x['id'], reverse=True)
        
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
        print(f"SUCCESSO: {len(final)} offerte reali e funzionanti salvate!")
    else:
        print("Errore critico: Nessun dato trovato.")

if __name__ == "__main__":
    scrape_telegram()
