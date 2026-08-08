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
            if res.status_code != 200: continue
            
            soup = BeautifulSoup(res.content, 'html.parser')
            messages = soup.select('div.tgme_widget_message')
            
            chan_count = 0
            for msg in messages:
                try:
                    text_el = msg.select_one('div.tgme_widget_message_text')
                    if not text_el: continue
                    text = text_el.get_text()
                    
                    links = msg.select('a')
                    amazon_url = ""
                    for link in links:
                        href = link.get('href', '')
                        if "amazon.it" in href or "amzn.to" in href:
                            amazon_url = href
                            break
                    if not amazon_url: continue
                    
                    img_el = msg.select_one('a.tgme_widget_message_photo_wrap')
                    if not img_el: continue
                    style = img_el.get('style', '')
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                    img_url = match.group(1) if match else ""
                    if not img_url: continue

                    price_match = re.search(r"(\d+([\.,]\d+)?)\s*€", text)
                    new_p = 0.0
                    if price_match:
                        nums = [g for g in price_match.groups() if g]
                        new_p = float(nums[0].replace(',', '.')) if nums else 0.0
                    
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
                        "asin": amazon_url.split('/')[-1].split('?')[0] or "B000000000",
                        "category": channel.capitalize()
                    })
                    chan_count += 1
                except: continue
            print(f"Trovate {chan_count} offerte.")
        except: continue
    
    if all_deals:
        unique = {d['url']: d for d in all_deals}.values()
        final = sorted(list(unique), key=lambda x: x['id'], reverse=True)
        with open("offerte.json", "w", encoding="utf-8") as f:
            json.dump(final, f, indent=2, ensure_ascii=False)
