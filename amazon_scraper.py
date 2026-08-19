import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

# CONFIGURAZIONE STANDARD PROFESSIONALE (Basata su progetti GitHub Top)
CHANNELS = ["offertone", "tariffando", "codiciscontopuntoit", "scontitech"]

def scrape_telegram():
    all_deals = []
    print("--- AVVIO BOT PROFESSIONALE STANDARD ---")
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            res = requests.get(url, headers=headers, timeout=20)
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.content, 'html.parser')
            messages = soup.select('div.tgme_widget_message')
            
            for msg in messages:
                try:
                    text_el = msg.select_one('div.tgme_widget_message_text')
                    if not text_el: continue
                    text = text_el.get_text()
                    
                    # Estrazione Link (Standard GitHub)
                    links = msg.select('a')
                    amazon_url = next((l.get('href') for l in links if "amazon.it" in l.get('href','') or "amzn.to" in l.get('href','')), "")
                    if not amazon_url: continue
                    
                    # Estrazione Immagine (Standard GitHub)
                    img_el = msg.select_one('a.tgme_widget_message_photo_wrap')
                    if not img_el: continue
                    style = img_el.get('style', '')
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                    img_url = match.group(1) if match else ""
                    
                    # Estrazione Prezzo (Regex Standard)
                    price_match = re.search(r"(\d+([\.,]\d+)?)\s*€", text)
                    if not price_match: continue
                    new_p = float(price_match.group(1).replace(',', '.'))
                    
                    all_deals.append({
                        "product_name": text.split('\n')[0][:100],
                        "deal_price": new_p,
                        "original_price": round(new_p * 1.3, 2),
                        "url": amazon_url,
                        "image": img_url,
                        "category": channel.capitalize()
                    })
                except: continue
        except: continue
    
    if all_deals:
        # Salvataggio nel formato universale richiesto
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(all_deals, f, indent=2, ensure_ascii=False)
        print(f"SUCCESSO: {len(all_deals)} offerte salvate.")

if __name__ == "__main__":
    scrape_telegram()
