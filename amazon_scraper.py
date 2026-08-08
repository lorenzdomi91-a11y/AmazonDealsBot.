import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

CHANNELS = ["offertone", "tariffando", "codiciscontopuntoit", "scontitech", "scontioffertait", "offertepuntotech", "hardwareofferte"]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}

def clean_title(t):
    t = re.sub(r"[^\w\s€%,\.\-\!]", "", t)
    t = re.sub(r"(?i)a soli.*", "", t)
    t = re.sub(r"(?i)minimo storico.*", "", t)
    return t.strip()

def scrape_telegram():
    all_deals = []
    print("--- AVVIO BOT GHOST PRO ---")
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        try:
            res = requests.get(url, headers=HEADERS, timeout=25)
            if res.status_code != 200: continue
            soup = BeautifulSoup(res.content, 'html.parser')
            messages = soup.select('div.tgme_widget_message')
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
                    if not price_match: continue
                    new_p = float(price_match.group(1).replace(',', '.'))
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
                        "asin": amazon_url.split('/')[-1].split('?')[0] or "B00000",
                        "category": channel.capitalize()
                    })
                except: continue
        except: continue
    
    # SALVATAGGIO FORZATO
    unique = {d['url']: d for d in all_deals}.values()
    final = sorted(list(unique), key=lambda x: x['id'], reverse=True)
    with open("offerte.json", "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)
    print(f"OPERAZIONE COMPLETATA: {len(final)} offerte salvate!")

if __name__ == "__main__":
    scrape_telegram()
