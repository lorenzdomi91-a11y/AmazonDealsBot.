import requests
from bs4 import BeautifulSoup
import json
import re
import time
import random

# LISTA MASSICCIA DI CANALI TELEGRAM (15 CANALI)
CHANNELS = [
    "offertone", "tariffando", "codiciscontopuntoit", 
    "scontitech", "scontioffertait", "offertepuntotech", 
    "hardwareofferte", "erroridiprezzo", "risparmiometro",
    "offertewow", "scontivolanti", "couponitalia",
    "prezzishock", "tempodicoupon", "affarissimi"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9"
}

def clean_title(t):
    # Rimuove emoji, scritte "A soli", "Minimo storico", etc.
    t = re.sub(r"(?i)a soli.*", "", t)
    t = re.sub(r"(?i)minimo storico.*", "", t)
    t = re.sub(r"(?i)offerta lampo.*", "", t)
    t = re.sub(r"[^\w\s€%,\.\-\!]", "", t)
    return t.strip()

def scrape_telegram():
    all_deals = []
    print("--- AVVIO BOT GHOST 6.0 (MAX VOLUME & EXTERNAL LINKS) ---")
    
    for channel in CHANNELS:
        url = f"https://t.me/s/{channel}"
        print(f"Scansione: {channel}...")
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
                    
                    # Estrazione Link Reale (Fondamentale)
                    links = msg.select('a')
                    amazon_url = ""
                    for link in links:
                        href = link.get('href', '')
                        # Cerchiamo solo link che portano a prodotti Amazon
                        if "amazon.it" in href or "amzn.to" in href:
                            # Evita link di risposta di Telegram o profili
                            if "t.me/" not in href:
                                amazon_url = href
                                break
                    
                    if not amazon_url: continue
                    
                    # Estrazione Immagine
                    img_el = msg.select_one('a.tgme_widget_message_photo_wrap')
                    if not img_el: continue
                    style = img_el.get('style', '')
                    match = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
                    img_url = match.group(1) if match else ""
                    if not img_url: continue

                    # Estrazione Prezzo
                    price_match = re.search(r"(\d+([\.,]\d+)?)\s*€", text)
                    if not price_match: continue
                    new_p = float(price_match.group(1).replace(',', '.'))
                    if new_p < 1.0: continue

                    # Dati calcolati
                    old_p = round(new_p * 1.3, 2)
                    
                    # Pulizia Titolo
                    full_title = text.split('\n')[0]
                    if len(full_title) < 10 and len(text.split('\n')) > 1:
                        full_title = text.split('\n')[1] # Prendi la seconda riga se la prima è corta (emoji)

                    all_deals.append({
                        "id": int(time.time()) + len(all_deals),
                        "title": clean_title(full_title),
                        "oldPrice": old_p,
