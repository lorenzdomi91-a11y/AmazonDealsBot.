import asyncio
import json
import time
import random
from playwright.async_api import async_playwright

URL_OFFERTE = "https://www.amazon.it/gp/goldbox"

async def scrape():
    async with async_playwright() as p:
        print("🚀 Lancio browser...")
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        
        print("🔗 Navigazione su Amazon...")
        await page.goto(URL_OFFERTE, wait_until="domcontentloaded", timeout=60000)
        
        # Scroll veloce
        for _ in range(2):
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(1)

        print("🧐 Estrazione...")
        deals = await page.evaluate("""() => {
            const results = [];
            document.querySelectorAll("[data-testid='deal-card']").forEach(el => {
                try {
                    const title = el.querySelector('h2, .deal-title').innerText;
                    const link = el.querySelector('a').href;
                    const img = el.querySelector('img').src;
                    const price = el.querySelector('.a-price-whole').innerText.replace(/[^0-9]/g, '');
                    results.push({
                        title: title,
                        url: link,
                        image: img,
                        newPrice: parseFloat(price),
                        oldPrice: parseFloat(price) * 1.3,
                        discountPct: 25,
                        category: "Offerta"
                    });
                } catch(e){}
            });
            return results;
        }""")
        
        await browser.close()
        
        if deals:
            with open("offerte.json", "w", encoding="utf-8") as f:
                json.dump(deals, f, indent=2, ensure_ascii=False)
            print(f"✅ Salvate {len(deals)} offerte!")
        else:
            print("❌ Nessuna offerta trovata.")

if __name__ == "__main__":
    asyncio.run(scrape())
