import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

CHANNELS = ["offertone", "tariffando", "codiciscontopuntoit", "scontitech"]

def scrape():
    all_deals = []
    print("--- AVVIO BOT GHOST 11.0 ---")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code != 200: continue
            soup = BeautifulSoup(res.content, 'html.parser')
            messages = soup.select('div.tgme_widget_message')
            for msg in messages:
                try:
                    text_el = msg.select_one('div.tgme_widget_message_text')
                    if not text_el: continue
                    text = text_el.get_text()
                    links = msg.select('a')
                    amazon_url = next((l.get('href') for l in links if "amazon.it" in l.get('href','') or "amzn.to" in l.get('href','')), None)
                    if not amazon_url: continue
                    
                    price_match = re.search(r"(\d+([\.,]\d+)?)\s*€", text)
                    if not price_match: continue
                    price = float(price_match.group(1).replace(',', '.'))
                    
                    img_el = msg.select_one('a.tgme_widget_message_photo_wrap')
                    img_url = ""
                    if img_el:
                        style = img_el.get('style', '')
                        img_url = re.search(r"url\(['\"]?(.*?)['\"]?\)", style).group(1)

                    all_deals.append({
                        "title": text.split('\n')[0][:100],
                        "price": price,
                        "oldPrice": round(price * 1.3, 2),
                        "url": amazon_url,
                        "image": img_url,
                        "category": channel
                    })
                except: continue
        except: continue

    if all_deals:
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(all_deals, f, indent=2, ensure_ascii=False)
        print(f"Salvate {len(all_deals)} offerte!")
    else:
        print("Nessun dato trovato.")

if __name__ == "__main__":
    scrape()
