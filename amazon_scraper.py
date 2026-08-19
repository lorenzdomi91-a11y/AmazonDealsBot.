import asyncio
import json
import time
import random
from playwright.async_api import async_playwright

URL_OFFERTE = "https://www.amazon.it/gp/goldbox"

async def scrape_amazon():
    async with async_playwright() as p:
        print("🚀 Avvio Browser Robotizzato...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("🔗 Navigazione su Amazon.it/offerte...")
        # Usiamo 'load' invece di 'networkidle' per guadagnare minuti
        await page.goto(URL_OFFERTE, wait_until="load", timeout=60000)
        
        print("⏳ Scorrimento pagina per caricare i prodotti...")
        for i in range(3):
            await page.mouse.wheel(0, 2000)
            await asyncio.sleep(1.5)

        print("🧐 Estrazione dati in corso...")
        deals = await page.evaluate("""() => {
            const results = [];
            const items = document.querySelectorAll("[data-testid='deal-card'], .a-section.deal-card");
            
            items.forEach(item => {
                try {
                    const titleEl = item.querySelector("h2, .deal-title, [data-testid='deal-card-title']");
                    const imgEl = item.querySelector("img");
                    const linkEl = item.querySelector("a");
                    const priceEl = item.querySelector(".a-price-whole");
                    const fractionEl = item.querySelector(".a-price-fraction");
                    const oldPriceEl = item.querySelector(".a-text-strike, .basis-price");
                    
                    if (titleEl && linkEl && priceEl) {
                        const priceText = priceEl.innerText.replace(/[^0-9]/g, '');
                        const fractionText = fractionEl ? fractionEl.innerText.replace(/[^0-9]/g, '') : "00";
                        const finalPrice = parseFloat(priceText + "." + fractionText);
                        
                        let oldPrice = finalPrice * 1.35;
                        if (oldPriceEl) {
                            const opText = oldPriceEl.innerText.replace(/[^0-9.,]/g, '').replace(',', '.');
                            oldPrice = parseFloat(opText) || oldPrice;
                        }

                        // CORREZIONE: 'push' invece di 'append'
                        results.push({
                            title: titleEl.innerText.trim(),
                            price: finalPrice,
                            old_price: oldPrice,
                            link: linkEl.href,
                            image: imgEl ? imgEl.src : ""
                        });
                    }
                } catch (e) {}
            });
            return results;
        }""")

        await browser.close()
        
        if deals:
            final_data = []
            for d in deals:
                if not d['link'].startswith("http"): continue
                discount = round(((d['old_price'] - d['price']) / d['old_price']) * 100) if d['old_price'] > d['price'] else 0
                
                final_data.append({
                    "id": str(time.time()) + str(random.randint(0,999)),
                    "title": d['title'],
                    "price": d['price'],
                    "old_price": d['old_price'],
                    "discountPct": discount,
                    "url": d['link'],
                    "image": d['image'],
                    "category": "Amazon Reale"
                })

            with open("offerte.json", "w", encoding="utf-8") as f:
                json.dump(final_data, f, indent=2, ensure_ascii=False)
            print(f"✅ COMPLETATO: {len(final_data)} offerte salvate!")
        else:
            print("❌ ERRORE: Nessuna offerta trovata. Amazon potrebbe aver cambiato i selettori.")

if __name__ == "__main__":
    asyncio.run(scrape_amazon())
