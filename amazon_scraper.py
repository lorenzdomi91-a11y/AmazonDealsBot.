import argparse
import json
import logging
import os
import random
import re
import time
import uuid
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Lista di User-Agent (aggiungi o modifica se vuoi)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

DEFAULT_HEADERS = {
    "Accept-Language": "it-IT,it;q=0.9",
    "Referer": "https://www.google.it/",
}


def make_session(retries=5, backoff_factor=1):
    session = requests.Session()
    retry = Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset(["GET", "POST"])
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(DEFAULT_HEADERS)
    return session


def rotate_user_agent(session):
    session.headers["User-Agent"] = random.choice(USER_AGENTS)


def clean_price_string(price_str):
    if not price_str:
        return 0.0
    s = "".join(c for c in price_str if c.isdigit() or c in ",.")
    if not s:
        return 0.0
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def is_blocked_page(soup, text):
    lower = text.lower()
    patterns = [
        "captcha",
        "bot",
        "accesso negato",
        "denied",
        "we have detected unusual traffic",
        "are you a robot",
        "enter the characters you see below",
    ]
    if any(p in lower for p in patterns):
        return True
    if soup.select_one("form[action*='captcha']") or soup.select_one("input[id='captchacharacters']"):
        return True
    return False


def parse_item(item):
    asin = item.get("data-asin") or ""
    if not asin:
        a = item.select_one("a[href*='/dp/']")
        if a and a.get("href"):
            m = re.search(r"/dp/([A-Z0-9]{6,})", a["href"])
            if m:
                asin = m.group(1)

    title_el = item.select_one("h2 span") or item.select_one("span.a-size-base-plus")
    title = title_el.get_text(strip=True) if title_el else "Prodotto Amazon"

    img_el = item.select_one("img.s-image")
    image = img_el.get("src") if img_el else ""

    price_new_container = item.select_one("span.a-price span.a-offscreen")
    price_alt = item.select_one("span.a-offscreen")
    new_p = clean_price_string(price_new_container.get_text() if price_new_container else (price_alt.get_text() if price_alt else ""))

    price_old_container = item.select_one("span.a-price.a-text-price span.a-offscreen") or item.select_one("span.a-text-strike")
    old_p = clean_price_string(price_old_container.get_text()) if price_old_container else 0.0

    if old_p == 0:
        data_price = item.get("data-price") or item.get("data-list-price")
        if data_price:
            old_p = clean_price_string(data_price)

    discount = 0
    try:
        if old_p > new_p and old_p > 0:
            discount = int(((old_p - new_p) / old_p) * 100)
    except Exception:
        discount = 0

    if discount < 0 or discount > 98:
        discount = 0
        old_p = new_p

    text = item.get_text(" ", strip=True).lower()
    has_coupon = "coupon" in text or "risparmia" in text

    return {
        "id": uuid.uuid4().hex,
        "asin": asin,
        "title": title,
        "image": image,
        "oldPrice": round(old_p, 2),
        "newPrice": round(new_p, 2),
        "discountPct": discount,
        "hasCoupon": has_coupon,
        "couponText": "COUPON DISPONIBILE" if has_coupon else "",
        "category": "Amazon",
        "description": f"Sconto reale del {discount}%" if discount > 0 else "",
        "scraped_at": datetime.utcnow().isoformat() + "Z",
    }


def scrape_page(session, url, min_discount=20, max_discount=97, timeout=20):
    logging.info("Scansione: %s", url)
    rotate_user_agent(session)
    try:
        r = session.get(url, timeout=timeout)
    except requests.RequestException as e:
        logging.warning("Request fallita per %s: %s", url, e)
        return []

    if r.status_code != 200:
        logging.warning("Status %s per %s", r.status_code, url)
        return []

    soup = BeautifulSoup(r.content, "html.parser")
    if is_blocked_page(soup, r.text):
        logging.error("Pagina bloccata o captcha per %s — interrompo parsing", url)
        return []

    items = soup.select('div[data-component-type="s-search-result"]')
    results = []
    for item in items:
        try:
            p = parse_item(item)
            if (p["discountPct"] >= min_discount and p["discountPct"] <= max_discount) or p["hasCoupon"]:
                results.append(p)
                logging.info("Trovato: %s - %s€ (sconto %s%%)", p["asin"], p["newPrice"], p["discountPct"])
        except Exception as e:
            logging.debug("Errore parsing item: %s", e)
            continue
    return results


def dedupe_by_asin(list_of_dicts):
    seen = {}
    for d in list_of_dicts:
        asin = d.get("asin") or d.get("title") or str(uuid.uuid4())
        if asin not in seen:
            seen[asin] = d
    return list(seen.values())


def main(urls, output, min_discount, max_discount, delay_min, delay_max):
    session = make_session()
    all_deals = []
    for url in urls:
        try:
            found = scrape_page(session, url, min_discount=min_discount, max_discount=max_discount)
            all_deals.extend(found)
        except Exception as e:
            logging.exception("Errore durante scraping di %s: %s", url, e)
        sleep_time = random.uniform(delay_min, delay_max)
        logging.debug("Sleep %.2fs", sleep_time)
        time.sleep(sleep_time)

    if not all_deals:
        logging.error("Nessuna offerta trovata. Controlla i selettori o se Amazon ti ha bloccato.")
        return 1

    unique = dedupe_by_asin(all_deals)
    final = sorted(unique, key=lambda x: x.get("scraped_at", ""), reverse=True)

    tmp = output + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    try:
        os.replace(tmp, output)
    except Exception:
        logging.warning("Impossibile fare replace atomico, scrivo direttamente.")
        with open(output, "w", encoding="utf-8") as f:
            json.dump(final, f, ensure_ascii=False, indent=2)

    logging.info("COMPLETATO: %d offerte salvate in %s", len(final), output)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Amazon deals scraper (più robusto)")
    parser.add_argument("--output", default="offerte.json", help="File di output JSON")
    parser.add_argument("--min-discount", type=int, default=20, help="Sconto minimo (%)")
    parser.add_argument("--max-discount", type=int, default=97, help="Sconto massimo (%)")
    parser.add_argument("--delay-min", type=float, default=4.0, help="Delay minimo tra richieste (s)")
    parser.add_argument("--delay-max", type=float, default=8.0, help="Delay massimo tra richieste (s)")
    parser.add_argument("--urls", nargs="*", help="URL da scansionare (se omessi usa valori di default)")
    args = parser.parse_args()

    TARGET_URLS = args.urls or [
        "https://www.amazon.it/s?k=offerte+lampo&i=specialty-aps&srs=11400615031&rh=p_8%3A20-95",
        "https://www.amazon.it/s?k=elettronica&i=electronics&rh=p_8%3A20-95",
        "https://www.amazon.it/s?k=informatica&i=computers&rh=p_8%3A20-95",
    ]

    exit_code = main(TARGET_URLS, args.output, args.min_discount, args.max_discount, args.delay_min, args.delay_max)
    if exit_code:
        raise SystemExit(exit_code)